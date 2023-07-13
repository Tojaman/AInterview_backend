from rest_framework import serializers

from speak_to_chat.serializers import ResponseVoiceSerializer
from users.models import User
from .models import Form


class FormsSerializer(serializers.ModelSerializer):
    class Meta:
        user_id = serializers.PrimaryKeyRelatedField(read_only=True)
        model = Form
        fields = '__all__'

class FormCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = ("sector_name", "job_name", "career", "resume")


# class UserSerializer(serializers.ModelSerializer):
#     forms = FormsSerializer(many=True,)
#
#     class Meta:
#         model=User
#         fields = (__all__)
