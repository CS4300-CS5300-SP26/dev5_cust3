from django.shortcuts import render

# Landing page view
def index(request):
    return render(request, "knowledge_map/index.html")

# Home page view
def homepage(request):
    return render(request, "knowledge_map/homepage.html")

# Upload content view 
def create_map(request):
    return render(request, "knowledge_map/create_map.html")

# Quiz view
def quiz(request):
    return render(request, "knowledge_map/quiz.html")

# Progress view
def progress(request):
    return render(request, "knowledge_map/progress.html")
