from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('homepage/', views.homepage, name='homepage'),
    path('upload/', views.upload, name='upload'),
    path('delete/<int:file_id>/', views.delete_file, name='delete_file'),
    path("delete-selected-files/", views.delete_selected_files, name="delete_selected_files"),
    path('maps/', views.maps, name='maps'),
    path('quizzes/', views.quizzes_hub, name='quizzes'),
    path('quiz/<int:pk>/', views.quiz_detail, name='quiz_detail'),
    path('quiz/<int:attempt_id>/results/', views.quiz_results, name='quiz_results'),
    path('progress/', views.progress, name='progress'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'),
    path('quiz/<int:pk>/delete/', views.delete_quiz, name='delete_quiz'),
    #path('logout/', views.logout, name='logout'),
]