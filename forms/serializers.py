from rest_framework import serializers

from speak_to_chat.serializers import ResponseVoiceSerializer
from .models import Form


class FormsSerializer(serializers.ModelSerializer):
    # questions = ResponseVoiceSerializer(many=True, read_only=True)
    class Meta:
        model = Form
        fields = ("sector_name", "job_name", "career", "resume")


class FormCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = ("sector_name", "job_name", "career", "resume")
