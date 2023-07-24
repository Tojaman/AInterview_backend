from django.urls import path, include

from .views import (
    QnAview,
    GPTAnswerView,
)

from django.urls import re_path
from .interview_consumer import InterviewConsumer


urlpatterns = [
    path("qna/", QnAview.as_view()),
    path("gptanswer/", GPTAnswerView.as_view()),
    re_path(r"interview/$", InterviewConsumer.as_asgi()),
]
