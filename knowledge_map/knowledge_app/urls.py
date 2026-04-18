from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('homepage/', views.homepage, name='homepage'),
    path('upload/', views.upload, name='upload'),
    path('upload/create-folder/', views.create_folder, name='create_folder'),
    path('upload/move-files/', views.move_files, name='move_files'),
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
    # path('logout/', views.logout, name='logout'),
    path('create-map/', views.create_map, name='create_map'),
    path('map/<int:map_id>/', views.view_map, name='view_map'),
    path('map/<int:map_id>/status/', views.map_status, name='map_status'),
    path('map/<int:map_id>/delete/', views.delete_map, name='delete_map'),
    path('map/<int:map_id>/related/', views.related_topics, name='related_topics'),
    path('profile/', views.user_profile, name='user_profile'),
    path('map/<int:map_id>/share/', views.share_map, name='share_map'),
    path('shared/<uuid:share_token>/', views.view_shared_map, name='view_shared_map'),
]