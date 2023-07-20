from __future__ import absolute_import, unicode_literals
from celery import shared_task
import openai
import os

# @shared_task : 데코레이터 -> 작업(Task)로 사용될 함수를 식별하고 등록
@shared_task
def process_whisper_data():
        # openai API Key를 .env 파일에서 가져옴
        #openAI_Api_key = env('openAI_Api_key')
        openAI_Api_key = os.getenv('OPENAI_API_KEY')

        # openai API 키 인증
        openai.api_key = openAI_Api_key
        
        # # whisper 폴더에 있는 audio.mp3 파일 경로를 audio_file 변수에 할당
        # audio_file = open(link, "rb")
        
        # 음성 답변 받기
        audio_file = request.FILES["voice_file"]
        form_id = request.data["form_id"]
        question_id = request.data["question_id"]
        
        # 음성 -> 텍스트
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        # transcript = openai.Audio.translate("whisper-1", audio_file)
        transcription = transcript['text']
        
        return transcription