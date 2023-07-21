from __future__ import absolute_import, unicode_literals
from celery import shared_task
import openai
import os

# @shared_task : 데코레이터 -> 작업(Task)로 사용될 함수를 식별하고 등록
@shared_task
def process_whisper_data(temp_file_path):
        # openai API Key를 .env 파일에서 가져옴
        #openAI_Api_key = env('openAI_Api_key')
        openAI_Api_key = os.getenv('OPENAI_API_KEY')

        # openai API 키 인증
        openai.api_key = openAI_Api_key
        
        # 음성 -> 텍스트
        with open(temp_file_path, "rb") as audio_file:
                transcript = openai.Audio.transcribe("whisper-1", audio_file)
        # transcript = openai.Audio.transcribe("whisper-1", audio_file)
        # transcript = openai.Audio.translate("whisper-1", audio_file)
        transcription = transcript['text']
        
        return transcription