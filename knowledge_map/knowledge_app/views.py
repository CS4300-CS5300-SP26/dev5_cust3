from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views import View
from django.db.models import Prefetch
from .services.quiz_generator import generate_quiz, generate_quiz_from_text

from .models import Quiz, Question, QuizAttempt, Answer, UploadedFile
from .forms import QuizGenerationForm
from .services.quiz_generator import generate_quiz

import pdfplumber
import os
import json

# Landing page view
def index(request):
    return render(request, "knowledge_app/index.html")

# use @login_required to force login before accessing a view

# delete file button view
#@login_required
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
#@login_required
def upload(request):
    if request.method == 'POST':
        # Get the file from the form
        file = request.FILES.get('pdf_file')
        
        if file and file.name.endswith('.pdf'):
            # Save file to database and disk
            uploaded = UploadedFile.objects.create(file=file)
            # Extract text from each page of the PDF
            text = ""
            try: 
                with pdfplumber.open(uploaded.file.path) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() or ""
            except Exception as e:
                pass

        # Redirect back to upload page after submission
        return redirect('upload')

    # Get all uploaded files from the database, newest first
    files = UploadedFile.objects.all().order_by('-uploaded_at')

    # Send files to the template so they appear in the list
    return render(request, "knowledge_app/upload.html", {'files': files})
#@login_required
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
def homepage(request):
    return render(request, "knowledge_app/homepage.html")

# Upload content view 
def maps(request):
    return render(request, "knowledge_app/maps.html")

# Quiz view
def quiz(request):
    return render(request, "knowledge_app/quiz.html")

# Progress view
def progress(request):
    return render(request, "knowledge_app/progress.html")

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
# Quiz logic
@login_required
def quizzes_hub(request):
    """
    Main quiz hub - displays all quizzes and generation form
    """
    if request.method == 'POST':
        form = QuizGenerationForm(request.POST, request.FILES, user=request.user)
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
                question_types=form.cleaned_data.get('question_types', ['multiple_choice', 'true_false']),
                difficulty=form.cleaned_data.get('difficulty', 'medium')
            )
            
            return redirect('quiz_detail', pk=quiz.id)
    else:
        form = QuizGenerationForm(user=request.user)
    
    # Get all user's quizzes with their latest attempt
    quizzes = Quiz.objects.filter(user=request.user).prefetch_related(
        'questions',
        Prefetch('attempts', queryset=QuizAttempt.objects.order_by('-created_at'))
    ).order_by('-created_at')
    
    return render(request, 'knowledge_app/quizzes.html', {
        'quizzes': quizzes,
        'form': form,
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
        short_answer_grades = grade_short_answers(short_answer_pairs) if short_answer_pairs else {}

        # Process each question's answer
        for question in questions:
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
        score = round((correct_count / total_questions * 100)) if total_questions > 0 else 0
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
    answers = attempt.answers.select_related('question').order_by('question__order')
    
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