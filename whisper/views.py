from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from .models import VoiceFile
from .serializers import VoiceFileSerializer
from drf_yasg.utils import swagger_auto_schema
from .open_api_params import get_params, post_params
from dotenv import load_dotenv
import os
import openai
import json

class VoiceFileView(APIView):
    @swagger_auto_schema(manual_parameters=get_params)
    def get(self, request):
        VoiceFiles = VoiceFile.objects.first() # VoiceFile 모델의 첫 번째 객체 가져옴
        if VoiceFiles is None:
            VoiceFiles = VoiceFile.objects.create()
        serializer = VoiceFileSerializer(VoiceFiles) # 가져온 객체를 직렬화(객체 -> JSON)

        load_dotenv()
        
        # openai API Key를 .env 파일에서 가져옴
        #openAI_Api_key = env('openAI_Api_key')
        openAI_Api_key = os.getenv('OPENAI_API_KEY')

        # openai API 키 인증
        openai.api_key = openAI_Api_key
        
        # whisper 폴더에 있는 audio.mp3 파일 경로를 audio_file 변수에 할당
        audio_file = open("whisper/audio.mp3", "rb")
        
        # 음성을 텍스트로 변환하고 변환된 텍스트를 transcription에 저장
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        transcription = transcript['text'] # txt로 변환한 내용
        
        # VoiceFile 모델의 transcription 인스턴스에 변환된 텍스트를 저장
        VoiceFiles.transcription = transcription
        VoiceFiles.save()
        
        # Response객체를 생성하여 데이터와 상태 코드 반환
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(request_body=post_params)
    def post(self, request):
        return Response("Swagger Schema")