from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('home/', views.home, name='home'),
    path('new_map/', views.create_map, name='create_map'),
    path('quiz/', views.quiz, name='quiz'),
    path('progress/', views.progress, name='progress'),
    path('logout/', views.logout_view, name='logout'),
]