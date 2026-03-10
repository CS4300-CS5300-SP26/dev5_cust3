from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('homepage/', views.homepage, name='homepage'),
    path('upload/', views.upload, name='upload'),
    path('maps/', views.maps, name='maps'),
    path('quiz/', views.quiz, name='quiz'),
    path('progress/', views.progress, name='progress'),
    # path('logout/', views.logout_view, name='logout'),
]