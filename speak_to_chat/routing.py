from django.urls import path, re_path
from .deep_interview_consumer import DeepInterviewConsumer
from .default_interview_consumer import DefaultInterviewConsumer


websocket_urlpatterns = [
    re_path(r"ws/deep-interview/$", DeepInterviewConsumer.as_asgi()),
    re_path(r"ws/default-interview/$", DeepInterviewConsumer.as_asgi()),
]
