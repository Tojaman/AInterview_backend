from django.urls import path, include
from .views import (
    DefaultInterview,
    SituationInterview,
    DeepInterview,

    PersonalityInterview,
    QnAview,
    GPTAnswerview,

)

urlpatterns = [
    path("default/", DefaultInterview.as_view()),
    path("situation/", SituationInterview.as_view()),
    path("deep/", DeepInterview.as_view()),

    path("personality/", PersonalityInterview.as_view()),
    path("qna/", QnAview.as_view()),
    path("gptanswer/", GPTAnswerview.as_view()),
]

