FROM python:3.11.4

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 설치
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 포트 설정 (필요에 따라 수정 가능)
EXPOSE 8000

# 컨테이너 실행 명령
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]