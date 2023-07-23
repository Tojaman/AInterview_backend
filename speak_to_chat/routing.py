from django.urls import path, re_path
from .deep_interview_consumer import DeepInterviewConsumer
from .default_interview_consumer import DefaultInterviewConsumer
from .situation_interview_consumer import SituationInterviewConsumer
from .personality_interview_consumer import PersonalityInterviewConsumer

websocket_urlpatterns = [
    re_path(r"ws/deep-interview/$", DeepInterviewConsumer.as_asgi()),
    re_path(r"ws/situation-interview/$", SituationInterviewConsumer.as_asgi()),
    re_path(r"ws/personality-interview/$", PersonalityInterviewConsumer.as_asgi()),
    re_path(r"ws/default-interview/$", DefaultInterviewConsumer.as_asgi()),
]
