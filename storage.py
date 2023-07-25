import os
import boto3
from dotenv import load_dotenv
import uuid

def get_audio_file_url(audio_file):
    load_dotenv()
    # AWS SDK 클라이언트 생성:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.environ.get("MY_AWS_ACCESS_KEY"),
        aws_secret_access_key=os.environ.get("MY_AWS_SECRET_ACCESS_KEY"),
    )
    audio_file_key = "record/" + str(uuid.uuid4()) + ".mp3"

    # 파일을 S3 버킷에 업로드
    s3_client.put_object(Body=audio_file, Bucket=os.environ.get("AWS_STORAGE_BUCKET_NAME"), Key=audio_file_key)
    # 업로드된 파일의 URL을 구성
    url = os.getenv("FILE_URL")+"/"+ audio_file_key

    # URL 문자열에서 공백을 "_"로 대체
    url = url.replace(" ", "_")
    
    return url

def get_image_file_url(image_file):
    load_dotenv()
    # AWS SDK 클라이언트 생성:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.environ.get("MY_AWS_ACCESS_KEY"),
        aws_secret_access_key=os.environ.get("MY_AWS_SECRET_ACCESS_KEY"),
    )
    image_file_key = "record/" + str(uuid.uuid4()) + ".jpg"

    # 파일을 S3 버킷에 업로드
    s3_client.put_object(Body=image_file, Bucket=os.environ.get("AWS_STORAGE_BUCKET_NAME"), Key=image_file_key)
    # 업로드된 파일의 URL을 구성
    url = os.getenv("FILE_URL")+"/"+ image_file_key

    # URL 문자열에서 공백을 "_"로 대체
    url = url.replace(" ", "_")
    
    return url