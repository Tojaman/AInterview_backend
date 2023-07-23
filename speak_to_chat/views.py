from urllib.parse import urlparse

import boto3
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from drf_yasg.utils import swagger_auto_schema
from dotenv import load_dotenv
import openai
import base64
from .tasks import process_whisper_data
from django.core.files.base import ContentFile
from .models import Answer, Question, GPTAnswer
import os
from .serializers import ResponseVoiceSerializer
from django.core.files.temp import NamedTemporaryFile
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import action
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from forms.models import Form
from .models import Question
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
import random
from django.http import HttpResponse
from django.http import JsonResponse

from .tasks import process_whisper_data
from ..ainterview.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME

load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")


# 특정 form의 질문, 답변, 음성파일 가져오기
class QnAview(APIView):
    @swagger_auto_schema(
        operation_description="지원 정보와 연결된 질문, 답변, 음성파일 받기",
        operation_id="질문, 답변, 음성파일 요청",
        manual_parameters=[
            openapi.Parameter(
                name="form_id",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=True,
                description="form_id",
            )
        ],
        responses={"200": ResponseVoiceSerializer},
    )
    # form_id와 연결되어 있는 question 객체를 가져온다.
    # form에 질문과 답변이 여러개 들어있으므로 모두 가져온 후 보여줄 수 있어야 한다.

    def get(self, request):
        form_id = request.GET.get("form_id")
        # form Object 얻기
        form_object = Form.objects.get(id=form_id)

        # 특정 form과 연결된 Question, Answer 객체 리스트로 얻기
        question_object = Question.objects.filter(form_id=form_object)

        QnA = []
        for i in range(0, len(question_object) - 1):  # ok
            answer_object = Answer.objects.get(question_id=question_object[i])  # ok

            # 질문, 답변내용, 음성파일 가져오기
            question = question_object[i].content
            answer = answer_object.content
            file_url = answer_object.recode_file

            #s3로부터 음성파일 받아오기
            record_data = self.get_record(file_url)

            QnA.append({"question": question, "answer": answer, "record": record_data})

        # QnA 리스트 JSON으로 변환
        QnA = {"QnA": QnA}

        return JsonResponse(QnA, status=status.HTTP_200_OK)

    def get_record(self, file_url):

        # S3에서 파일을 가져옵니다.
        parsed_url = urlparse(file_url)
        file_key = parsed_url.path.lstrip("/")

        # AWS SDK 클라이언트 생성:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

        try:
            # 파일을 S3 버킷에서 가져오기
            response = s3_client.get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=file_key)

            # 파일 데이터 반환
            file_data = response['Body'].read()

            # 파일 데이터를 Base64로 인코딩하여 문자열로 변환
            encoded_data = base64.b64encode(file_data).decode('utf-8')

            return encoded_data

        except Exception as e:
            # 오류 처리
            print(f"오류 발생: {e}")
            return "파일을 불러올 수 없습니다."


class GPTAnswerview(APIView):
    @swagger_auto_schema(
        operation_description="지원 정보와 연결된 질문, 답변, GPT 답변 받기",
            operation_id="질문, 답변, gpt답변 요청.",
        manual_parameters=[
            openapi.Parameter(
                name="form_id",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=True,
                description="form_id",
            )
        ],
        responses={"200": ResponseVoiceSerializer},
    )
    def get(self, request):
        form_id = request.GET.get("form_id")
        # form Object 얻기
        form_object = Form.objects.get(id=form_id)

        # 특정 form과 연결된 Question 객체 리스트로 얻기
        question_object = Question.objects.filter(form_id=form_object)

        QnA = []
        for i in range(0, len(question_object) - 1):  # ok
            answer_object = Answer.objects.get(question_id=question_object[i])
            gptanswer_object = GPTAnswer.objects.get(question_id=question_object[i])

            # 질문, 답변 텍스트 가져오기
            question_content = question_id = question_object[i].content
            answer_content = answer_object.content
            gpt_answer = gptanswer_object.content

            QnA.append(
                {
                    "question": question_content,
                    "answer": answer_content,
                    "gptanswer": gpt_answer,
                }
            )

        # QnA 리스트 JSON으로 변환
        QnA = {"QnA": QnA}

        return JsonResponse(QnA, status=status.HTTP_200_OK)
