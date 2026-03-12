from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm

# Landing page view
def index(request):
    return render(request, "knowledge_app/index.html")

# us @login_required to force login before accessing a view
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
