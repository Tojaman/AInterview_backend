from django.urls import path, include
from . import views

urlpatterns = [
    path('post/', views.PostApplication.as_view()),
]