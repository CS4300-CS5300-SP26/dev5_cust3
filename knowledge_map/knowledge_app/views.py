from django.shortcuts import render, redirect, get_object_or_404
from .models import UploadedFile
import pdfplumber
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .services.quiz_generator import generate_quiz
from django.views import View
import os

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

def quiz_view(request):
    # mock topics till we get some real data 
    topics = [
        {
            "topic_id": 1,
            "keywords": ["CPU", "processing", "instructions", "register", "ALU"],
            "sentences": [
                "The CPU processes instructions in a computer system.",
                "It uses registers to store temporary data.",
                "The ALU performs arithmetic operations."
            ]
        },
        {
            "topic_id": 2,
            "keywords": ["memory", "RAM", "storage", "data", "cache"],
            "sentences": [
                "Memory stores data for quick access.",
                "RAM is volatile memory used during execution.",
                "Cache improves performance by storing frequently used data."
            ]
        }
    ]

    quiz = generate_quiz(topics)
    score = None

    if request.method == "POST":
        score = 0

        for q in quiz:
            user_answer = request.POST.get(q['id'])

            if q['type'] == "true_false":
                user_answer = user_answer == "True"

            if user_answer == q.get("answer"):
                score += 1

    return render(request, "knowledge_app/quiz.html", {
        "quiz": quiz,
        "score": score
    })