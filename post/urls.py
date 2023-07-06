from django.urls import path, include
from . import views

urlpatterns = [
    path('post/<int:post_id>', views.PostApplication.as_view()),
]