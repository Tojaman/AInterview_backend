from django.db import models

class VoiceFile(models.Model):
    #audio_file = models.FileField(upload_to='./audio.mp3')
    #audio_file = models.FileField(upload_to="", null=True)
    transcription = models.TextField(blank=True)
    gpt_answer = models.TextField(blank=True)