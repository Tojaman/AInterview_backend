from channels.generic.websocket import WebsocketConsumer
import openai
from .models import Form
from dotenv import load_dotenv
import os
import json
from .models import Form, Question, Answer
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
import tempfile
import base64

load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")


class DeepInterviewConsumer(WebsocketConsumer):
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

            temp_file.close()

            # 임시 파일 삭제
            os.unlink(temp_file_path)
        # 대답만 추가하는 경우
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
                "content": 'function_name: [interviewee_info] input: ["Company", "Job", "Career"] rule: [Please act as a skillful interviewer. We will provide the input form including "Company," "Professional," and "Career." Look at the sentences "Company," "Job," and "Career" to get information about me as an interview applicant. For example, let\'s say company = IT company, job = web front-end developer, experience = newcomer. Then you can recognize that you\'re a newbie applying to an IT company as a web front-end developer. And you can ask questions that fit this information. You must speak only in Korean during the interview. You can only ask questions. You can\'t answer.]'
                + 'function_name: [aggresive_position] rule: [Ask me questions in a tail-to-tail manner about what I answer. There may be technical questions about the answer, and there may be questions that you, as an interviewer, would dig into the answer.. For example, if the question asks, "What\'s your web framework?" the answer is, "It is React framework." So the new question is, "What do you use as a state management tool in React, and why do you need this?" It should be the same question. If you don\'t have any more questions, move on to the next topic.] '
                + 'function_name: [self_introduction] input : ["self-introduction"] rule: [We will provide an input form including a "self-introduction." Read this "self-introduction" and extract the content to generate a question. just ask one question. Don\'t ask too long questions. The question must have a definite purpose. and Just ask one question at a time.'
                + 'interviewee_info(Company="'
                + selector_name
                + '", Job="'
                + job_name
                + '", Career="'
                + career
                + '")'
                + 'self_introduction("'
                + resume
                + '")'
                + "aggressive_position()",
            }
        ]
