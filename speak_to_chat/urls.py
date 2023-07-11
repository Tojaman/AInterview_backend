from django.urls import path, include
from .views import DefaultInterview, SituationInterview, DeepInterview, TendancyInterview

urlpatterns = [
    path('default/', DefaultInterview.as_view()),
    path('situation/', SituationInterview.as_view()),
    path('deep/', DeepInterview.as_view()),
    path('tendancy/', TendancyInterview.as_view())
]

