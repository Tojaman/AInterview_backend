from django.urls import path, include

from .views import (
    QnAview,
    GPTAnswerview,

)

from django.urls import re_path
from .deep_interview_consumer import DeepInterviewConsumer
from .situation_interview_consumer import SituationInterviewConsumer
from .personality_interview_consumer import PersonalityInterviewConsumer
from .default_interview_consumer import DefaultInterviewConsumer


    


urlpatterns = [
    path("qna/", QnAview.as_view()),
    path("gptanswer/", GPTAnswerview.as_view()),
    re_path(r"deep-interview/$", DeepInterviewConsumer.as_asgi()),
    re_path(r"situation-interview/$", SituationInterviewConsumer.as_asgi()),
    re_path(r"personality-interview/$", PersonalityInterviewConsumer.as_asgi()),
    re_path(r"default-interview/$", DefaultInterviewConsumer.as_asgi()),
]

