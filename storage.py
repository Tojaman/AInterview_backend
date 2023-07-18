from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def upload_mp3(mp3_file, file_path):
    # S3에 파일 업로드
    default_storage.save(file_path, mp3_file.read())

    # 업로드된 파일의 URL 가져오기
    file_url = default_storage.url(file_path)

    return file_url