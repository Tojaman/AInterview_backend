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
from .models import Answer
import os
from .serializers import RequestVoiceSerializer,ResponseVoiceSerializer

load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")


# 기본 인터뷰
class DefaultInterview(APIView):
    
    # 처음 데이터를 받아야 하는 경우 -> 음성 데이터는 없음. 그냥 GPT 질문 시작.
    @swagger_auto_schema(responses={"200":ResponseVoiceSerializer})
    def get(self, request):
        self.conversation = []
        
        # 대화 시작 메시지 추가
        self.conversation.append(
            {
                "role": "user",
                "content": "Let's do a job interview simulation. You're an interviewer and I'm an applicant. When I ask you to start taking interview, then start asking questions. I will say the phrase “start the interview” for you to start. Ask one question at a time. Then, ask another question after I provided the answer. Continue this process until I ask you to stop. Please say 'Yes' if you understood my instructions.",
            }
        )
        self.conversation.append(
            {
                "role": "assistant",
                "content": "Yes. I am playing the role of the interviewer. I'll do my best.",
            }
        )
        self.conversation.append(
            {
                "role": "user",
                "content": "You can only ask me some questions from now on. Don't say anything other than a question. Please just say 'Explain the applicant.' if you understood my instructions.",
            }
        )
        self.conversation.append(
            {"role": "assistant", "content": "Explain the applicant."}
        )
        self.conversation.append(
            {
                "role": "user",
                "content": "Start the interview. I will apply to Naver as a front-end developer. Also, Start the interview. I will apply to Naver as a front-end developer. Remember. I am applying for the first time in this field. ",
            },
        )
        
        self.conversation.append(
            {
                "role":"assistant",
                "content": "ok. I understand."
            }
        )
        
        self.conversation.append(
            {
                "role": "user",
                "content": "please ask me the questions one at a time. And answer only the question you created by translating them into Korean. Don't answer in English."
            }
        )
        
        self.conversation.append(
            {
                "role":"assistant",
                "content": "ok. I understand."
            }
        )
        
        self.conversation.append(
            {
                "role":"user",
                "content": "Please prepare challenging and common question for interviewers when applying for Naver Front Developer."
            }
        )
        
        # 대화 계속하기
        message = self.continue_conversation()
        
        return Response(message, status=status.HTTP_200_OK)
    
    
    # 음성 데이터를 받아야 하는 경우
    @swagger_auto_schema(query_serializer=RequestVoiceSerializer, responses={"200":ResponseVoiceSerializer})
    def post(self, request):
        
        self.conversation = []
        
        
        

        #     # 답변을 받고, 응답을 해주는 부분 -> 음성 파일 추출 필요
            
            
        #     # 음성 파일을 body로 부터 추출하고, wav 파일로 저장.
        #     base64_audio = request.POST.get('audio_data')
        #     if base64_audio:
        #         audio_data = base64.b64decode(base64_audio)
        #         file = ContentFile(audio_data, name='audio.wav')
            
        
        #     self.conversation.append(
        #         {
        #             "role": "user",
        #             "content": "Let's do a job interview simulation. You're an interviewer and I'm an applicant. When I ask you to start taking interview, then start asking questions. I will say the phrase “start the interview” for you to start. Ask one question at a time. Then, ask another question after I provided the answer. Continue this process until I ask you to stop. Please say 'Yes' if you understood my instructions.",
        #         }
        #     )
        #     self.conversation.append(
        #         {
        #             "role": "assistant",
        #             "content": "Yes. I am playing the role of the interviewer. I'll do my best.",
        #         }
        #     )
        #     self.conversation.append(
        #         {
        #             "role": "user",
        #             "content": "You can only ask me some questions from now on. Don't say anything other than a question. Please just say 'Explain the applicant.' if you understood my instructions.",
        #         }
        #     )
        #     self.conversation.append(
        #         {"role": "assistant", "content": "Explain the applicant."}
        #     )
        #     self.conversation.append(
        #         {
        #             "role": "user",
        #             "content": "Start the interview. I will apply to Naver as a front-end developer. Also, I am a new front-end applicant. Please prepare challenging and common questions for interviewers when applying for Naver Front Developer. If I answer, tell me okay and present me the next question you prepared earlier. Now ask the question.",
        #         },
        #     )

        #     # Response객체를 생성하여 데이터와 상태 코드 반환
        #     return Response(message, status=status.HTTP_200_OK)
    
    
        



    def continue_conversation(self):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.conversation,
            temperature=0.9,
            n=1
        )

        message = completion.choices[0].message['content']
        return message 
    


# 상황 부여 면접 
class SituationInterview(APIView):
    # 처음 데이터를 받아야 하는 경우 -> 음성 데이터는 없음. 그냥 GPT 질문 시작.
    @swagger_auto_schema(responses={"200":ResponseVoiceSerializer})
    def get(self, request):
        self.conversation = []
        
        # 대화 시작 메시지 추가
        self.conversation.append(
            {
                "role": "user",
                "content": "Let's do a job interview simulation. You're an interviewer and I'm an applicant. When I ask you to start taking interview, then start asking questions. I will say the phrase “start the interview” for you to start. Ask one question at a time. Then, ask another question after I provided the answer. Continue this process until I ask you to stop. Please say 'Yes' if you understood my instructions.",
            }
        )
        self.conversation.append(
            {
                "role": "assistant",
                "content": "Yes. I am playing the role of the interviewer. I'll do my best.",
            }
        )
        self.conversation.append(
            {
                "role": "user",
                "content": "You can only ask me some questions from now on. Don't say anything other than a question. Please just say 'Explain the applicant.' if you understood my instructions.",
            }
        )
        self.conversation.append(
            {"role": "assistant", "content": "Explain the applicant."}
        )
        self.conversation.append(
            {
                "role": "user",
                "content": "Start the interview. I will apply to Naver as a front-end developer. Also, I am a new front-end applicant.",
            },
        )
        self.conversation.append(
            {
                "role":"assistant",
                "content" : "ok. i understand."
            }
        )
        self.conversation.append(
            {
                "role":"user",
                "content": "Create appropriate situational interview questions based on the position of front-end developer. Ask one question at a time. Don't even say yes, just ask questions."
            }
        )
        # 대화 계속하기
        message = self.continue_conversation()
        
        return Response(message, status=status.HTTP_200_OK)
    
    def continue_conversation(self):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.conversation,
            temperature=0.9,
            n=1,
        )

        message = completion.choices[0].message['content']
        return message 
    


# 심층 면접 인터뷰
class DeepInterview(APIView):
    
    # 처음 데이터를 받아야 하는 경우 -> 음성 데이터는 없음. 그냥 GPT 질문 시작.
    @swagger_auto_schema(responses={"200":ResponseVoiceSerializer})
    def get(self, request):
        self.conversation = []
        
        # 대화 시작 메시지 추가
        self.conversation.append(
            {
                "role": "user",
                "content": "Let's do a job interview simulation. You're an interviewer and I'm an applicant. When I ask you to start taking interview, then start asking questions. I will say the phrase “start the interview” for you to start. Then, ask another question after I provided the answer. Continue this process until I ask you to stop. Please say 'Yes' if you understood my instructions.",
            }
        )
        self.conversation.append(
            {
                "role": "assistant",
                "content": "Yes. I am playing the role of the interviewer. I'll do my best.",
            }
        )
        self.conversation.append(
            {
                "role": "user",
                "content": "You can only ask me some questions from now on. Don't say anything other than a question. Please just say 'Explain the applicant.' if you understood my instructions.",
            }
        )
        self.conversation.append(
            {"role": "assistant", "content": "Explain the applicant."}
        )
        self.conversation.append(
            {
                "role": "user",
                "content": "Start the interview. I will apply to Naver as a front-end developer. Also, I am a new front-end applicant. Please prepare challenging and common questions for interviewers when applying for Naver Front Developer. If I answer, tell me okay and present me the next question you prepared earlier. Now ask the question.",
            },
        )
        # 대화 계속하기
        message = self.continue_conversation()
        
        return Response(message, status=status.HTTP_200_OK)
    
    def continue_conversation(self):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.conversation,
            temperature=0.9,
            n=1
        )

        message = completion.choices[0].message['content']
        return message 
    


# 성향 면접 인터뷰  
class TendancyInterview(APIView):
    
    # 처음 데이터를 받아야 하는 경우 -> 음성 데이터는 없음. 그냥 GPT 질문 시작.
    @swagger_auto_schema(responses={"200":ResponseVoiceSerializer})
    def get(self, request):
        self.conversation = []
        
        # 대화 시작 메시지 추가
        self.conversation.append(
            {
                "role": "user",
                "content": "Let's do a job interview simulation. You're an interviewer and I'm an applicant. When I ask you to start taking interview, then start asking questions. I will say the phrase “start the interview” for you to start. Ask one question at a time. Then, ask another question after I provided the answer. Continue this process until I ask you to stop. Please say 'Yes' if you understood my instructions.",
            }
        )
        self.conversation.append(
            {
                "role": "assistant",
                "content": "Yes. I am playing the role of the interviewer. I'll do my best.",
            }
        )
        self.conversation.append(
            {
                "role": "user",
                "content": "You can only ask me some questions from now on. Don't say anything other than a question. Please just say 'Explain the applicant.' if you understood my instructions.",
            }
        )
        self.conversation.append(
            {"role": "assistant", "content": "Explain the applicant."}
        )
        self.conversation.append(
            {
                "role": "user",
                "content": "Start the interview. I will apply to Naver as a front-end developer. Also, I am a new front-end applicant. Please prepare challenging and common questions for interviewers when applying for Naver Front Developer. If I answer, tell me okay and present me the next question you prepared earlier. Now ask the question.",
            },
        )
        # 대화 계속하기
        message = self.continue_conversation()
        
        return Response(message, status=status.HTTP_200_OK)
    
    def continue_conversation(self):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.conversation,
            temperature=0.9,
            n=1
        )

        message = completion.choices[0].message['content']
        return message 
    
    