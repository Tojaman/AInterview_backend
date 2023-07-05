from rest_framework import serializers
from .models import VoiceFile

class VoiceFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceFile # Meta 클래스 내에 model 속성을 설정하여 VoiceFile 모델과 연결
        # fields = ('id', 'file', 'transcription') # 직렬화 할 필드 지정
        fields = '__all__'
        #read_only_fields = ('transcription') # 변환된 텍스트를 읽기 전용으로 설정(잘못된 변경 방지?)