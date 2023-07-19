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

load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")


# 특정 form의 질문, 답변 가져오기(get으로 가져오기)
class QnAview(APIView):
    @swagger_auto_schema(
        operation_description="지원 정보와 연결된 질문, 답변 받기",
        operation_id="form_id를 입력해주세요.",
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

            # 질문, 답변 텍스트 가져오기
            question = question_object[i].content
            answer = answer_object.content

            QnA.append({"question": question, "answer": answer})

        # QnA 리스트 JSON으로 변환
        QnA = {"QnA": QnA}

        return JsonResponse(QnA, status=status.HTTP_200_OK)


class GPTAnswerview(APIView):
    @swagger_auto_schema(
        operation_description="지원 정보와 연결된 질문, 답변, GPT 답변 받기",
        operation_id="form_id를 입력해주세요.",
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
