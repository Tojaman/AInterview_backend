from django.urls import path, include
from .views import VoiceFileView #, PostVoiceFile

urlpatterns = [
    path('voicefiles/', VoiceFileView.as_view()),
    #path('post/', PostVoiceFile.as_view()),
    #url(r'^data_analysis/uploadfile/$', 'blog.data_analysis.upload_file'),
]