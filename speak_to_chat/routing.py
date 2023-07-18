from django.urls import path, re_path
from .deep_interview_consumer import DeepInterviewConsumer


websocket_urlpatterns = [
    re_path(r"ws/deep-interview/$", DeepInterviewConsumer.as_asgi()),
]
