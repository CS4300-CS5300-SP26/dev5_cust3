from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import UploadedFile, KnowledgeMap
from .tasks import generate_knowledge_map
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views import View
from django.db.models import Prefetch, Count, Q
from .services.quiz_generator import generate_quiz, generate_quiz_from_text
from django.views.decorators.http import require_POST
from .models import Quiz, Question, QuizAttempt, Answer, UploadedFile, UserProfile, Folder
from openai import OpenAI
from .forms import QuizGenerationForm

import pdfplumber
import os
import json

from .models import KnowledgeMap, SharedMap, TopicNode, NodeRelationship
from django.contrib.auth.models import User
from django.urls import reverse

# Landing page view

def index(request):
    return render(request, "knowledge_app/index.html")

# use @login_required to force login before accessing a view
# delete file button view
@login_required
def delete_selected_files(request):
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_files")

        if selected_ids:
            files_to_delete = UploadedFile.objects.filter(id__in=selected_ids)

            for f in files_to_delete:
                # delete the actual file from storage first
                if f.file:
                    f.file.delete(save=False)

                # delete the database row
                f.delete()

    return redirect("upload")

#Upload view
@login_required
def upload(request):
    if request.method == 'POST':
        file = request.FILES.get('pdf_file')

        if file and file.name.endswith('.pdf'):
            original_name = file.name
            uploaded = UploadedFile(file=file, original_filename=original_name, user=request.user)
            uploaded.save()

            text = ""
            try:
                with pdfplumber.open(uploaded.file.path) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() or ""
            except Exception:
                pass

            uploaded.extracted_text = text
            uploaded.save()

        return redirect('upload')

    query = request.GET.get('q', '')
    folder_id = request.GET.get('folder', '')
    folders = Folder.objects.filter(user=request.user)

    files = UploadedFile.objects.filter(user=request.user)
    if query:
        files = files.filter(
            Q(original_filename__icontains=query) |
            Q(extracted_text__icontains=query)
        )
    if folder_id == 'none':
        files = files.filter(folder__isnull=True)
    elif folder_id:
        files = files.filter(folder__id=folder_id)

    files = files.order_by('-uploaded_at')

    return render(request, "knowledge_app/upload.html", {
        'files': files,
        'query': query,
        'folders': folders,
        'active_folder': folder_id,
    })

#folder mangemnt views
def create_folder(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            Folder.objects.get_or_create(user=request.user, name=name)
    return redirect('upload')


def move_files(request):
    if request.method == 'POST':
        file_ids = request.POST.getlist('selected_files')
        folder_id = request.POST.get('target_folder')

        folder = None
        if folder_id:
            try:
                folder = Folder.objects.get(id=folder_id, user=request.user)
            except Folder.DoesNotExist:
                pass

        UploadedFile.objects.filter(
            id__in=file_ids,
            user=request.user
        ).update(folder=folder)

    return redirect('upload')


@login_required
def delete_file(request, file_id):

    # Get the file or return 404 if it doesn't exist
    uploaded = get_object_or_404(UploadedFile, id=file_id)

    # Delete the actual file from disk
    if os.path.exists(uploaded.file.path):
        os.remove(uploaded.file.path)

    # Delete the record from the database
    uploaded.delete()

    # Redirect back to upload page
    return redirect('upload')

# Home page view
@login_required
def homepage(request):
    files = UploadedFile.objects.all().order_by('-uploaded_at')
    return render(request, "knowledge_app/homepage.html", {'files': files})

# Stored maps view
@login_required
def maps(request):
    user_maps = KnowledgeMap.objects.filter(user=request.user)\
        .select_related('uploaded_file')\
        .prefetch_related('topics')\
        .annotate(topic_count=Count('topics'))\
        .order_by('-created_at')

    # Maps shared with user by other users
    shared_with_me = SharedMap.objects.filter(
        shared_with=request.user
    ).select_related('knowledge_map', 'knowledge_map__user')

    return render(request, "knowledge_app/maps.html", {
        'maps': user_maps,
        'shared_with_me': shared_with_me,
    })
    
# Quiz view
@login_required
def quiz(request):
    return render(request, "knowledge_app/quiz.html")

# Progress view
@login_required
def progress(request):
    from django.db.models import Avg
    quizzes = Quiz.objects.filter(user=request.user).prefetch_related('attempts', 'questions')

    quiz_data = []
    for quiz in quizzes:
        latest = quiz.latest_attempt

        if latest is None:
            status = 'not_attempted'
        elif latest.score >= 80:
            status = 'mastered'
        elif latest.score >= 60:
            status = 'learning'
        else:
            status = 'needs_practice'

        # Per-question-type breakdown from latest attempt
        type_breakdown = {}
        if latest:
            for answer in latest.answers.select_related('question'):
                qtype = answer.question.get_question_type_display()
                if qtype not in type_breakdown:
                    type_breakdown[qtype] = {'correct': 0, 'total': 0}
                type_breakdown[qtype]['total'] += 1
                if answer.is_correct:
                    type_breakdown[qtype]['correct'] += 1
            for t in type_breakdown:
                d = type_breakdown[t]
                d['pct'] = round(d['correct'] / d['total'] * 100) if d['total'] else 0

        all_attempts = quiz.attempts.all()
        highest_score = max((a.score for a in all_attempts), default=None)
        attempts_list = list(all_attempts.order_by('-created_at'))
        previous_score = attempts_list[1].score if len(attempts_list) > 1 else None
        trend_diff = round(latest.score - previous_score) if previous_score is not None and latest else None

        quiz_data.append({
            'quiz': quiz,
            'status': status,
            'latest_score': latest.score if latest else None,
            'attempts': quiz.total_attempts,
            'avg_score': quiz.average_score,
            'highest_score': highest_score,
            'type_breakdown': type_breakdown,
            'previous_score': previous_score,
            'trend_diff': trend_diff,
        })

    # Summary stats
    total = len(quiz_data)
    mastered = sum(1 for q in quiz_data if q['status'] == 'mastered')
    learning = sum(1 for q in quiz_data if q['status'] == 'learning')
    needs_practice = sum(1 for q in quiz_data if q['status'] == 'needs_practice')
    not_attempted = sum(1 for q in quiz_data if q['status'] == 'not_attempted')
    mastery_pct = round((mastered / total) * 100) if total > 0 else 0
    
    return render(request, 'knowledge_app/progress.html', {
        'quiz_data': quiz_data,
        'total': total,
        'mastered': mastered,
        'learning': learning,
        'needs_practice': needs_practice,
        'not_attempted': not_attempted,
        'mastery_pct': mastery_pct,
    })

# Login view
def Login(request):
    return render(request, "knowledge_app/login.html")

# Register view
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

# User profile and settings page view
@login_required
def user_profile(request):
    user = request.user
    upload_count = UploadedFile.objects.filter(user=user).count()
    quiz_attempts = QuizAttempt.objects.filter(user=user)
    total_quizzes = quiz_attempts.count()
    average_score = round(
        sum(a.score for a in quiz_attempts) / total_quizzes, 1
    ) if total_quizzes > 0 else 0

    return render(request, "knowledge_app/user_profile.html", {
        'user': user,
        'upload_count': upload_count,
        'total_quizzes': total_quizzes,
        'average_score': average_score,
    })

# Quiz logic


@login_required
def quizzes_hub(request):
    """
    Main quiz hub - displays all quizzes and generation form
    """
    if request.method == 'POST':
        form = QuizGenerationForm(
            request.POST, request.FILES, user=request.user)
        if form.is_valid():
            # Generate quiz from PDF or text
            quiz = form.save(commit=False)
            quiz.user = request.user

            # Handle different source types
            source_choice = form.cleaned_data['source_choice']
            if source_choice == 'existing':
                quiz.source_file = form.cleaned_data['existing_pdf']
            elif source_choice == 'upload':
                # Create new UploadedFile for the uploaded PDF
                uploaded_file = UploadedFile.objects.create(
                    user=request.user,
                    file=form.cleaned_data['pdf_file']
                )
                quiz.source_file = uploaded_file
            elif source_choice == 'text':
                quiz.source_text = form.cleaned_data['text_input']

            quiz.save()

            # Extract text and generate questions using OpenAI
            text = ""

            # If the user selected an existing or newly uploaded PDF option then extract
            if source_choice == 'existing' or source_choice == 'upload':
                import pdfplumber
                try:
                    # Open the PDF and extract text from each page
                    with pdfplumber.open(quiz.source_file.file.path) as pdf:
                        for page in pdf.pages:
                            text += page.extract_text() or ""
                except Exception as e:
                    print(f"PDF extraction error: {e}")

            # If the user pasted text directly then use that
            elif source_choice == 'text':
                text = form.cleaned_data.get('text_input', '')

            # Send the extracted text to OpenAI to generate quiz questions
            generate_quiz_from_text(
                quiz=quiz,
                text=text,
                num_questions=form.cleaned_data.get('num_questions', 5),
                question_types=form.cleaned_data.get(
                    'question_types', ['multiple_choice', 'true_false']),
                difficulty=form.cleaned_data.get('difficulty', 'medium')
            )

            return redirect('quiz_detail', pk=quiz.id)
    else:
        form = QuizGenerationForm(user=request.user)
        preselected = request.GET.get('existing_pdf')
        if preselected:
            # Validate the file belongs to the current user before trusting it
            file = UploadedFile.objects.filter(user=request.user, pk=preselected).first()
            if file:
                form.fields['existing_pdf'].initial = file.pk
                form.fields['source_choice'].initial = 'existing'
    

    # Get all user's quizzes with their latest attempt
    quizzes = Quiz.objects.filter(user=request.user).prefetch_related(
        'questions',
        Prefetch('attempts', queryset=QuizAttempt.objects.order_by('-created_at'))
    ).order_by('-created_at')

    return render(request, 'knowledge_app/quizzes.html', {
        'quizzes': quizzes,
        'form': form,
        'preselected_pdf': request.GET.get('existing_pdf'),
})
 


@login_required
def quiz_detail(request, pk):
    """
    Display quiz details, previous attempts, and quiz form
    """
    quiz = get_object_or_404(Quiz, pk=pk, user=request.user)

    if request.method == 'POST':
        # Process quiz submission
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=request.user,
            correct_count=0,
            total_questions=quiz.questions.count()
        )

        questions = list(quiz.questions.all())
        correct_count = 0
        total_questions = len(questions)

        # Collect all short answer questions to batch grade in one OpenAI call
        short_answer_pairs = [
            (q, request.POST.get(f'q_{q.id}', '').strip(), q.correct_answer)
            for q in questions if q.question_type == 'short_answer'
        ]

        # Grade all short answers in one OpenAI call
        from .services.quiz_generator import grade_short_answers
        short_answer_grades = grade_short_answers(
            short_answer_pairs) if short_answer_pairs else {}

        # Process each question's answer
        for question in questions:
            if question.question_type == 'matching':
                # Collect all matching answers into one string
                matching_answers = []
                for i, pair in enumerate(question.pairs, start=1):
                    answer_val = request.POST.get(f'q_{question.id}_{i}', '')
                    matching_answers.append(
                        f"{pair['premise']} → {answer_val}")
                user_answer = ' | '.join(matching_answers)
            else:
                user_answer = request.POST.get(f'q_{question.id}', '').strip()

            # Use OpenAI grade for short answer, normal check for everything else
            if question.question_type == 'short_answer':
                is_correct = short_answer_grades.get(question.id, False)
            else:
                is_correct = check_answer(question, user_answer)

            if is_correct:
                correct_count += 1

            # Save the answer
            Answer.objects.create(
                attempt=attempt,
                question=question,
                user_answer=user_answer,
                correct_answer=question.correct_answer,
                is_correct=is_correct
            )

        # Update attempt with final score
        score = round((correct_count / total_questions * 100)
                      ) if total_questions > 0 else 0
        attempt.score = score
        attempt.correct_count = correct_count
        attempt.total_questions = total_questions
        attempt.save()

        return redirect('quiz_results', attempt_id=attempt.id)

    # Get all previous attempts and render the quiz detail page
    attempts = quiz.attempts.order_by('-created_at')
    return render(request, 'knowledge_app/quiz_detail.html', {
        'quiz': quiz,
        'attempts': attempts,
    })


@login_required
def quiz_results(request, attempt_id):
    """
    Display results of a completed quiz attempt
    """
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=request.user)
    quiz = attempt.quiz

    # Get all answers for this attempt with related questions
    answers = attempt.answers.select_related(
        'question').order_by('question__order')

    return render(request, 'knowledge_app/quiz_results.html', {
        'attempt': attempt,
        'quiz': quiz,
        'answers': answers,
    })


def check_answer(question, user_answer):
    """
    Check if user's answer is correct based on question type
    """
    if not user_answer:
        return False

    user_answer = user_answer.strip().lower()
    correct = question.correct_answer.strip().lower()

    if question.question_type in ['multiple_choice', 'fill_in_blank', 'true_false']:
        # Exact match for these types
        return user_answer == correct

    elif question.question_type == 'short_answer':
        # Fuzzy matching for short answers (you might want to improve this)
        return similar_enough(user_answer, correct)

    elif question.question_type == 'matching':
        # For matching, this would be handled differently (multiple answers per question)
        return user_answer == correct

    return False


def similar_enough(str1, str2, threshold=0.8):
    """
    Check if two strings are similar enough (for short answer tolerance)
    You can use difflib.SequenceMatcher for more sophisticated matching
    """
    from difflib import SequenceMatcher
    ratio = SequenceMatcher(None, str1, str2).ratio()
    return ratio >= threshold


@login_required
def delete_quiz(request, pk):
    # Only allow deletion via POST request for security
    if request.method == 'POST':
        # Try to get the quiz, if it doesn't exist just redirect
        try:
            quiz = Quiz.objects.get(pk=pk, user=request.user)
            quiz.delete()
        except Quiz.DoesNotExist:
            pass

    # Redirect back to the quizzes hub
    return redirect('quizzes')

# Create map view - lets user select a PDF and trigger map generation


@login_required
def create_map(request):
    if request.method == 'POST':
        print(f"Creating map for user: {request.user}")
        file_id = request.POST.get('file_id')
        title = request.POST.get('title')

        # Get the uploaded file
        uploaded_file = get_object_or_404(UploadedFile, id=file_id)

        # Create a knowledge map record in the database
        knowledge_map = KnowledgeMap.objects.create(
            user=request.user,
            uploaded_file=uploaded_file,
            title=title,
            status='pending'
        )

        # Trigger the background Celery task
        generate_knowledge_map.delay(knowledge_map.id)

        # Redirect to the map view page
        return redirect('view_map', map_id=knowledge_map.id)

    # Get all uploaded files for the current user
    files = UploadedFile.objects.all().order_by('-uploaded_at')
    return render(request, 'knowledge_app/create_map.html', {'files': files})


# View map - renders the knowledge map using Cytoscape.js
@login_required
def view_map(request, map_id):
    knowledge_map = get_object_or_404(
        KnowledgeMap, id=map_id, user=request.user)

    # Get all topic nodes and relationships for this map
    topics = knowledge_map.topics.all()
    relationships = knowledge_map.relationships.all()

    # Build Cytoscape.js nodes
    nodes = [
        {'data': {'id': str(topic.id), 'label': topic.label,
                  'summary': topic.summary}}
        for topic in topics
    ]

    # Build Cytoscape.js edges
    edges = [
        {
            'data': {
                'id': f"e{rel.id}",
                'source': str(rel.source_topic.id),
                'target': str(rel.target_topic.id),
                'label': rel.relationship_label
            }
        }
        for rel in relationships
    ]

    return render(request, 'knowledge_app/view_map.html', {
        'knowledge_map': knowledge_map,
        'nodes': nodes,
        'edges': edges,
    })

# API endpoint to check map generation status
@login_required
def map_status(request, map_id):
    knowledge_map = get_object_or_404(
        KnowledgeMap, id=map_id, user=request.user)
    return JsonResponse({'status': knowledge_map.status})

# Delete map view
@login_required
def delete_map(request, map_id):
    if request.method == 'POST':
        knowledge_map = get_object_or_404(
            KnowledgeMap, id=map_id, user=request.user)
        knowledge_map.delete()
    return redirect('maps')

# Update theme view
@login_required
@require_POST
def update_theme(request):
    data = json.loads(request.body)
    dark_mode = data.get('dark_mode', False)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.dark_mode = dark_mode
    profile.save()
    return JsonResponse({'status': 'ok', 'dark_mode': dark_mode})

#related topics

def related_topics(request, map_id):
    knowledge_map = get_object_or_404(KnowledgeMap, id=map_id, user=request.user)
    
    topic_labels = list(knowledge_map.topics.values_list('label', flat=True))
    
    client = OpenAI()  # uses OPENAI_API_KEY env var
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a research assistant. Given a list of knowledge map topics, suggest 5-8 related research areas or articles the user might want to explore. Return JSON: {\"suggestions\": [{\"title\": str, \"description\": str, \"search_query\": str}]}"
            },
            {
                "role": "user", 
                "content": f"Topics: {', '.join(topic_labels)}"
            }
        ],
        response_format={"type": "json_object"}
    )
    
    data = json.loads(response.choices[0].message.content)
    return JsonResponse(data)

# Share map view
@login_required
def share_map(request, map_id):
    knowledge_map = get_object_or_404(KnowledgeMap, id=map_id, user=request.user)

    if request.method == 'POST':
        share_type = request.POST.get('share_type')

        if share_type == 'public':
            # get or create public share link
            shared_map, created = SharedMap.objects.get_or_create(
                knowledge_map=knowledge_map,
                is_public=True,
                shared_with=None
            )
            return JsonResponse({
                'share_url': request.build_absolute_uri(
                    reverse('view_shared_map', args=[shared_map.share_token])
                )
            })
        elif share_type == 'user':
            username = request.POST.get('username', '').strip()
            try:
                user_to_share_with = User.objects.get(username=username)
            except User.DoesNotExist:
                return JsonResponse({'error': f'User "{username}" not found'}, status=404)

            # Don't allow sharing with yourself
            if user_to_share_with == request.user:
                return JsonResponse({'error': 'You cannot share a map with yourself'}, status=400)

            # Get or create share for this specific user
            shared_map, created = SharedMap.objects.get_or_create(
                knowledge_map=knowledge_map,
                shared_with=user_to_share_with,
                defaults={'is_public': False}
            )
            return JsonResponse({
                'message': f'Map shared with {username} successfully'
            })

    # GET - show share options
    public_share = SharedMap.objects.filter(
        knowledge_map=knowledge_map,
        is_public=True
    ).first()

    shared_users = SharedMap.objects.filter(
        knowledge_map=knowledge_map,
        is_public=False
    ).exclude(shared_with=None)

    return render(request, 'knowledge_app/share_map.html', {
        'knowledge_map': knowledge_map,
        'public_share': public_share,
        'shared_users': shared_users,
    })

# View a shared map — accessible via public token or if shared with the user
def view_shared_map(request, share_token):
    shared_map = get_object_or_404(SharedMap, share_token=share_token)

    # Check access — public link or shared with logged in user
    if not shared_map.is_public:
        if not request.user.is_authenticated:
            return redirect(f'/accounts/login/?next={request.path}')
        if shared_map.shared_with != request.user:
            return HttpResponse('You do not have access to this map.', status=403)

    knowledge_map = shared_map.knowledge_map
    topics = knowledge_map.topics.all()
    relationships = knowledge_map.relationships.all()

    nodes = [
        {'data': {'id': str(topic.id), 'label': topic.label, 'summary': topic.summary}}
        for topic in topics
    ]
    edges = [
        {
            'data': {
                'id': f"e{rel.id}",
                'source': str(rel.source_topic.id),
                'target': str(rel.target_topic.id),
                'label': rel.relationship_label
            }
        }
        for rel in relationships
    ]

    return render(request, 'knowledge_app/view_shared_map.html', {
        'knowledge_map': knowledge_map,
        'nodes': nodes,
        'edges': edges,
        'shared_map': shared_map,
    })

# Add new topic node to a map
@login_required
def add_node(request, map_id):
    if request.method == 'POST':
        knowledge_map = get_object_or_404(KnowledgeMap, id=map_id, user=request.user)

        data = json.loads(request.body)
        label = data.get('label', '').strip()
        summary = data.get('summary', '').strip()

        if not label:
            return JsonResponse({'error': 'Label is required'}, status=400)

        node = TopicNode.objects.create(
            knowledge_map=knowledge_map,
            label=label,
            summary=summary
        )

        return JsonResponse({
            'id': str(node.id),
            'label': node.label,
            'summary': node.summary
        })

    return JsonResponse({'error': 'Method not allowed'}, status=405)

# delete topic node
@login_required
def delete_node(request, map_id, node_id):
    if request.method == 'POST':
        knowledge_map = get_object_or_404(KnowledgeMap, id=map_id, user=request.user)
        node = get_object_or_404(TopicNode, id=node_id, knowledge_map=knowledge_map)
        node.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Method not allowed'}, status=405)

    # Add a relationship between two nodes
@login_required
def add_relationship(request, map_id):
    if request.method == 'POST':
        knowledge_map = get_object_or_404(KnowledgeMap, id=map_id, user=request.user)

        data = json.loads(request.body)
        source_id = data.get('source_id')
        target_id = data.get('target_id')
        label = data.get('label', '').strip()

        if not source_id or not target_id:
            return JsonResponse({'error': 'Source and target nodes are required'}, status=400)

        if not label:
            return JsonResponse({'error': 'Relationship label is required'}, status=400)

        source_node = get_object_or_404(TopicNode, id=source_id, knowledge_map=knowledge_map)
        target_node = get_object_or_404(TopicNode, id=target_id, knowledge_map=knowledge_map)

        # Prevent duplicate relationships
        if NodeRelationship.objects.filter(
            knowledge_map=knowledge_map,
            source_topic=source_node,
            target_topic=target_node
        ).exists():
            return JsonResponse({'error': 'Relationship already exists'}, status=400)

        relationship = NodeRelationship.objects.create(
            knowledge_map=knowledge_map,
            source_topic=source_node,
            target_topic=target_node,
            relationship_label=label
        )

        return JsonResponse({
            'id': f"e{relationship.id}",
            'source': str(source_node.id),
            'target': str(target_node.id),
            'label': label
        })

    return JsonResponse({'error': 'Method not allowed'}, status=405)

# Delete a relationship between two nodes
@login_required
def delete_relationship(request, map_id, relationship_id):
    if request.method == 'POST':
        knowledge_map = get_object_or_404(KnowledgeMap, id=map_id, user=request.user)
        relationship = get_object_or_404(NodeRelationship, id=relationship_id, knowledge_map=knowledge_map)
        relationship.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Method not allowed'}, status=405)
