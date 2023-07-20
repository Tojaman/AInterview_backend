from channels.generic.websocket import WebsocketConsumer
import openai

#from ainterview.settings import FILE_URL
from storage import upload_mp3
from .models import Form, Answer
from dotenv import load_dotenv
import os
import json
from .models import Form, Question
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
import tempfile
import base64

load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")


class SituationInterviewConsumer(WebsocketConsumer):
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
            )

            # 대화 계속하기
            self.continue_conversation(form_object)
        elif data["type"] == "withAudio":
            # base64 디코딩
            audio_blob = data["audioBlob"]
            audio_data = base64.b64decode(audio_blob)

            # 오디오 파일로 변환
            audio_file = ContentFile(audio_data)

            # # s3업로드시 파일 경로 설정
            # file_name = audio_file.name
            # file_path = f'{FILE_URL}{file_name}'

            # # 파일 업로드 및 URL 받아오기
            # file_url = upload_mp3(audio_file, file_path)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_file_path = temp_file.name

            with open(temp_file_path, "wb") as file:
                for chunk in audio_file.chunks():
                    file.write(chunk)

            # 텍스트 파일로 변환
            with open(temp_file_path, "rb") as audio_file:
                transcript = openai.Audio.transcribe("whisper-1", audio_file)

            transcription = transcript["text"]

            # Question 테이블의 마지막 Row 가져오기
            last_low = Question.objects.latest("question_id")

            # 답변 테이블에 추가
            Answer.objects.create(content=transcription, question_id=last_low)
            # Answer.objects.create(
            #     content=transcription, question_id=last_low, recode_file=file_url
            # )
            print(transcription)

            # formId를 통해서 question 테이블을 가져옴
            form_object = Form.objects.get(id=data["formId"])
            questions = form_object.questions.all()

            self.default_tuning(
                form_object.sector_name,
                form_object.job_name,
                form_object.career,
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

            temp_file.close()

            # 임시 파일 삭제
            os.unlink(temp_file_path)
        else:
            # base64 디코딩
            audio_blob = data["audioBlob"]
            audio_data = base64.b64decode(audio_blob)

            # 오디오 파일로 변환
            audio_file = ContentFile(audio_data)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_file_path = temp_file.name

            with open(temp_file_path, "wb") as file:
                for chunk in audio_file.chunks():
                    file.write(chunk)

            # 텍스트 파일로 변환
            with open(temp_file_path, "rb") as audio_file:
                transcript = openai.Audio.transcribe("whisper-1", audio_file)

            transcription = transcript["text"]

            # Question 테이블의 마지막 Row 가져오기
            last_low = Question.objects.latest("question_id")

            # 답변 테이블에 추가
            Answer.objects.create(content=transcription, question_id=last_low)

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
    def default_tuning(self, seletor_name, job_name, career):
        # 대화 시작 메시지 추가
        self.conversation.append(
            {
                "role": "user",
                "content": 'function_name: [situation_interview] input: ["sector", "job", "career"] rule: [You are an expert in recruitment and interviewer specializing in finding the best talent. Ask questions that can judge my ability to cope with situations based “job” that I’ll provide and ask once at a time. For example, you would be ask such as "You have been assigned to work on a project where the design team has provided you with a visually appealing but intricate UI design for a web page. As you start implementing it, you realize that some of the design elements may not be feasible to achieve with the current technology or may negatively impact the performance. How would you handle this situation?" You should ask the next question only after I have answered to the question. Never ask a question similar to the previous one include example that i provide. Do not include any explanations or additional information in your response, simply provide a question in korean. Do not say anything other than a question.]'
                + "situation_interview(Company="
                + seletor_name
                + ", Job="
                + job_name
                + ", Career="
                + career
                + ")",
            }
        )
