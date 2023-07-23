import boto3
from dotenv import load_dotenv
import os

def get_file_url(data, uid):
    # AWS SDK 클라이언트 생성:
    # s3_client = boto3.client(
    #     's3',
    #     aws_access_key_id=AWS_ACCESS_KEY_ID,
    #     aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    # )
    # file_key = "record/" + uuid + ".mp3"

    # # 파일을 S3 버킷에 업로드
    # s3_client.put_object(Body=data, Bucket=AWS_STORAGE_BUCKET_NAME, Key=file_key)

    # # 업로드된 파일의 URL을 구성
    # url = FILE_URL +"/"+ file_key

    # # URL 문자열에서 공백을 "_"로 대체
    # url = url.replace(" ", "_")
    # return url
    load_dotenv()
    # AWS SDK 클라이언트 생성:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.environ.get("MY_AWS_ACCESS_KEY"),
        aws_secret_access_key=os.environ.get("MY_AWS_SECRET_ACCESS_KEY"),
    )
    file_key = "record/" + uid + ".mp3"

    # 파일을 S3 버킷에 업로드
    s3_client.put_object(Body=data, Bucket=os.environ.get("AWS_STORAGE_BUCKET_NAME"), Key=file_key)
    # 업로드된 파일의 URL을 구성
    url = os.getenv("FILE_URL")+"/"+ file_key

    # URL 문자열에서 공백을 "_"로 대체
    url = url.replace(" ", "_")
    return url