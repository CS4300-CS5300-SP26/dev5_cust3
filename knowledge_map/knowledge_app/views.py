from django.shortcuts import render, redirect, get_object_or_404
from .models import UploadedFile, KnowledgeMap
from .tasks import generate_knowledge_map
from django.http import JsonResponse
import pdfplumber
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
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

            # Save extracted text
            uploaded.extracted_text = text
            uploaded.save()

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

# Stored maps view 
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

# Create map view - lets user select a PDF and trigger map generation
@login_required
def create_map(request):
    if request.method == 'POST':
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
    knowledge_map = get_object_or_404(KnowledgeMap, id=map_id, user=request.user)

    # Get all topic nodes and relationships for this map
    topics = knowledge_map.topics.all()
    relationships = knowledge_map.relationships.all()

    # Build Cytoscape.js nodes
    nodes = [
        {'data': {'id': str(topic.id), 'label': topic.label, 'summary': topic.summary}}
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
    knowledge_map = get_object_or_404(KnowledgeMap, id=map_id, user=request.user)
    return JsonResponse({'status': knowledge_map.status})