from django.urls import path, re_path
from .interview_consumer import InterviewConsumer


websocket_urlpatterns = [
    re_path(r"ws/interview/$", InterviewConsumer.as_asgi()),
]
