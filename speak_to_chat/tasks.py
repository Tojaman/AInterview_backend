from __future__ import absolute_import, unicode_literals
from celery import shared_task
import openai
import os
from dotenv import load_dotenv
import boto3
import tempfile

load_dotenv()
openAI_Api_key = os.environ.get('GPT_API_KEY')
openai.api_key = openAI_Api_key
# @app.task
@shared_task
def process_whisper_data(s3_file_url, uid):
        s3_client = boto3.client(
                's3',
                aws_access_key_id=os.environ.get("MY_AWS_ACCESS_KEY"),
                aws_secret_access_key=os.environ.get("MY_AWS_SECRET_ACCESS_KEY"),
        )
        
        file_key = "record/" + uid + ".mp3"
        
        # S3 버킷에서 파일 데이터 가져오기
        response = s3_client.get_object(Bucket=os.environ.get("AWS_STORAGE_BUCKET_NAME"), Key=file_key)
        file_data = response['Body'].read()
        
        # file_data = byte 객체 -> name 속성이 존재하지 않아서 whisper에서 받을 수 없음
        # 이 문제를 회피하기 위해서 name 속성이 존재하는 tempfile로 만든 후 whisper에게 전달
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_file_path = temp_file.name
        
        with open(temp_file_path, "wb") as file:
                file.write(file_data)
        
        with open(temp_file_path, "rb") as audio_file:
                transcript = openai.Audio.transcribe("whisper-1", audio_file)
        
        transcription = transcript['text']
        
        return transcription