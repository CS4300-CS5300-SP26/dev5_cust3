from django.shortcuts import render

# Landing page view
def index(request):
    return render(request, "index.html")
