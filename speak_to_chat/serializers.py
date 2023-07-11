from rest_framework import serializers

class RequestVoiceSerializer(serializers.Serializer):
    voice_file = serializers.CharField(max_length=10000)

class ResponseVoiceSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()