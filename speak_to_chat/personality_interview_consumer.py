import uuid

from channels.generic.websocket import WebsocketConsumer
import openai

from storage import get_file_url
from .models import Form
from dotenv import load_dotenv
import os
import json
from .models import Form, Question, Answer, GPTAnswer
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
import tempfile
import base64
from .tasks import process_whisper_data

from .gpt_answer import add_gptanswer

load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")


class PersonalityInterviewConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        # 대화 기록을 저장할 리스트
        self.conversation = []

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        data = json.loads(text_data)

        print(data["formId"])
        print(data["type"])

        # 오디오 파일이 없는 경우
        if data["type"] == "withoutAudio":
            form_object = Form.objects.get(id=data["formId"])

            # 기본 튜닝
            self.default_tuning(
                form_object.sector_name,
                form_object.job_name,
                form_object.career,
                form_object.resume,
            )

            # 대화 계속하기
            self.continue_conversation(form_object)
        elif data["type"] == "withAudio":
            # base64 디코딩
            audio_blob = data["audioBlob"]
            audio_data = base64.b64decode(audio_blob)

            # 오디오 파일로 변환
            audio_file = ContentFile(audio_data)

            # 오디오 파일 이름 설정
            uid = str(uuid.uuid4())
            
            # s3에 파일 업로드 및 URL 받아오기
            file_url = get_file_url(audio_file, uid)

            # celery에 temp_file_path 전달해서 get()을 통해 동기적으로 실행(결과가 올 때까지 기다림)
            transcription = process_whisper_data.delay(file_url, uid).get()

            # Question 테이블의 마지막 Row 가져오기
            last_low = Question.objects.latest("question_id")

            # 답변 테이블에 추가
            Answer.objects.create(
                content=transcription, question_id=last_low, recode_file=file_url
            )
            answer_object = Answer.objects.latest("answer_id")
            
            print(transcription)

            # formId를 통해서 question 테이블을 가져옴
            form_object = Form.objects.get(id=data["formId"])
            questions = form_object.questions.all()

            self.default_tuning(
                form_object.sector_name,
                form_object.job_name,
                form_object.career,
                form_object.resume,
            )

            # question 테이블에서 질문과 답변에 대해 튜닝 과정에 추가함.
            try:
                for question in questions:
                    answer = question.answer
                    self.add_question_answer(question.content, answer.content)
            except:
                error_message = "같은 지원 양식의 question 테이블과 answer 테이블의 갯수가 일치하지 않습니다."
                print(error_message)

            self.continue_conversation(form_object)

        # 대답만 추가하는 경우
        else:
            # base64 디코딩
            audio_blob = data["audioBlob"]
            audio_data = base64.b64decode(audio_blob)

            # 오디오 파일로 변환
            audio_file = ContentFile(audio_data)
            
            # 오디오 파일 이름 설정
            uid = str(uuid.uuid4())

            # 파일 업로드 및 URL 받아오기
            file_url = get_file_url(audio_file, uid)

            # celery에 temp_file_path 전달해서 get()을 통해 동기적으로 실행(결과가 올 때까지 기다림)
            transcription = process_whisper_data.delay(file_url, uid).get()

            # Question 테이블의 마지막 Row 가져오기
            last_low = Question.objects.latest("question_id")

            # 답변 테이블에 추가
            Answer.objects.create(
                content=transcription, question_id=last_low, recode_file=file_url
            )
            answer_object = Answer.objects.latest("answer_id")

    # 질문과 대답 추가
    def add_question_answer(self, question, answer):
        existing_content = self.conversation[0]["content"]  # 기존 content 가져오기
        new_content = existing_content + " Q. " + question + " A. " + answer
        self.conversation[0]["content"] = new_content

    def continue_conversation(self, form_object):
        messages = ""
        for chunk in openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.conversation,
            temperature=0.7,
            stream=True,
        ):
            finish_reason = chunk.choices[0].finish_reason
            if chunk.choices[0].finish_reason == "stop":
                self.send(json.dumps({"message": "", "finish_reason": finish_reason}))
                break

            message = chunk.choices[0].delta["content"]
            messages += message
            # 메시지를 클라이언트로 바로 전송
            self.send(json.dumps({"message": message, "finish_reason": finish_reason}))

        Question.objects.create(content=messages, form_id=form_object)

    # 기본 튜닝
    def default_tuning(self, selector_name, job_name, career, resume):
        # 대화 시작 메시지 추가
        self.conversation = [
            {
                "role": "user",
                "content": 'function_name: [personality_interview] input: ["sector", "job", "career", "resume", "number_of_questions"] rule: [I want you to act as a strict interviewer, asking personality questions for the interviewee. I will provide you with input forms including "sector", "job", "career", "resume", and "number_of_questions". I have given inputs, but you do not have to refer to those. Your task is to simply make common personality questions and provide questions to me. You should create total of "number_of_questions" amount of questions, and provide it once at a time. You should ask the next question only after I have answered to the question. Do not include any explanations or additional information in your response, simply provide the generated question. You should also provide only one question at a time. Example questions would be questions such as "How do you handle stress and pressure?", "If you could change one thing about your personality, what would it be and why?". Remember, these questions are related to personality. Once all questions are done, you should just say "수고하셨습니다." You must speak only in Korean during the interview.] personality_interview('
                + str(selector_name)
                + ", "
                + str(job_name)
                + ", "
                + str(career)
                + ", "
                + str(resume)
                + ", 3)",
            }
        ]
