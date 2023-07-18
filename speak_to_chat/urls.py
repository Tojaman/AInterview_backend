from django.urls import path, include
from .views import (
    DefaultInterview,
    SituationInterview,
    DeepInterview,

    PersonalityInterview,
    QnAview,
    GPTAnswerview,

)

from django.urls import re_path
from .deep_interview_consumer import DeepInterviewConsumer


urlpatterns = [
    path("situation/", SituationInterview.as_view()),
    path("personality/", PersonalityInterview.as_view()),
    path("qna/", QnAview.as_view()),
    path("gptanswer/", GPTAnswerview.as_view()),
    re_path(r"deep-interview/$", DeepInterviewConsumer.as_asgi()),
    re_path(r"default-interview/$", DefaultInterviewConsumer.as_asgi()),
]

