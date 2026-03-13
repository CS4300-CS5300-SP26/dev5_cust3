from django.shortcuts import render, redirect
from .models import UploadedFile
import pdfplumber

# Landing page view
def index(request):
    return render(request, "knowledge_app/index.html")

def upload(request):

    # Handle form submission
    if request.method == 'POST':

        # Get the file from the form
        file = request.FILES.get('pdf_file')

        # Only allow PDF files
        if file and file.name.endswith('.pdf'):

            # Save file to database and disk
            uploaded = UploadedFile.objects.create(file=file)

            # Extract text from each page of the PDF
            text = ""
            with pdfplumber.open(uploaded.file.path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""

            # Temporary - print extracted text to terminal to confirm it works
            print(text)

        # Redirect back to upload page after submission
        return redirect('upload')

    # Get all uploaded files from the database, newest first
    files = UploadedFile.objects.all().order_by('-uploaded_at')

    # Send files to the template so they appear in the list
    return render(request, "knowledge_app/upload.html", {'files': files})

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
