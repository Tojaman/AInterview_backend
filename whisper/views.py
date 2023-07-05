from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from .models import VoiceFile
from .serializers import VoiceFileSerializer
import openai
import json

class VoiceFileView(APIView):
    def get(self, request):
        VoiceFiles = VoiceFile.objects.first() # VoiceFile 모델의 첫 번째 객체 가져옴
        serializer = VoiceFileSerializer(VoiceFiles) # 가져온 객체를 직렬화(객체 -> JSON)

        # ------------------------ openai API 키 숨기는 코드 ------------------------
        secret_file = 'whisper/secrets.json'
        with open(secret_file) as f:
            secrets = json.loads(f.read()) # secrets.json 파일을 파이썬 객체로 변환

        def get_secret(setting, secrets=secrets):
            try:
                return secrets[setting]
            except KeyError:
                error_msg = "Set the {} environment variable".format(setting)
                raise ImproperlyConfigured(error_msg)

        # 발급받은 API 키 설정
        OPENAI_API_KEY = get_secret("openAI_Api_key")

        # openai API 키 인증
        openai.api_key = OPENAI_API_KEY
        
        # whisper 폴더에 있는 audio.mp3 파일 경로를 audio_file 변수에 할당
        audio_file = open("whisper/audio.mp3", "rb")
        
        # 음성을 텍스트로 변환하고 변환된 텍스트를 transcription에 저장
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        transcription = transcript['text'] # txt로 변환한 내용
        
        # VoiceFile 모델의 transcription 인스턴스에 변환된 텍스트를 저장
        VoiceFiles.transcription = transcription
        VoiceFiles.save()
        
        # data 딕셔너리 생성하여 변환된 텍스트 저장
        data = {
            #'voice_file': serializer.data,
            'transcription': transcription
        }
        
        # Response객체를 생성하여 데이터와 상태 코드 반환
        return Response(serializer.data, status=status.HTTP_200_OK)