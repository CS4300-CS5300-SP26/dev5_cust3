from django.shortcuts import render

# Landing page view
def index(request):
    return render(request, "knowledge_app/index.html")

# Upload view
def upload(request):
    return render(request, "knowledge_app/upload.html")

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
