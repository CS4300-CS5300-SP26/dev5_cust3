from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('homepage/', views.homepage, name='homepage'),
    path('upload/', views.upload, name='upload'),
    path('delete/<int:file_id>/', views.delete_file, name='delete_file'),
    path("delete-selected-files/", views.delete_selected_files, name="delete_selected_files"),
    path('maps/', views.maps, name='maps'),
    path('quiz/', views.quiz_view, name='quiz'),
    path('progress/', views.progress, name='progress'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'),
    #path('logout/', views.logout, name='logout'),
]