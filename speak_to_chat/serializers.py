from rest_framework import serializers


class ResponseVoiceSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()