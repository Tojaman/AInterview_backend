from channels.generic.websocket import WebsocketConsumer
import openai
from dotenv import load_dotenv
from storage import get_file_url
import uuid
import os
import json
from .models import Question, Answer, GPTAnswer
from forms.models import Form
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
import tempfile
import base64

from .tasks import process_whisper_data

load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")


class DefaultInterviewConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        # 대화 기록을 저장할 리스트
        self.conversation = []

    def disconnect(self, close_code):
        

        print(self.question_number) 
        print(self.form_id)
        form_object = Form.objects.get(id=self.form_id)
        # 만약에 중간에 끊킨 경우, form_id와 관련된 것 전부 삭제
        questions = Question.objects.filter(form_id=form_object)
        question_numbers = questions.count()
        print(question_numbers)
        
        if question_numbers != self.question_number:
            Question.objects.filter(form_id=self.form_id).delete()
        
        for question in questions:
            try:
                answer = question.answer
                print(answer)
            except:
                Question.objects.filter(form_id=self.form_id).delete() 
        pass


    def receive(self, text_data):
        data = json.loads(text_data)

        
        self.form_id = data["formId"]
        self.question_number = data["questionNum"]


        # 오디오 파일이 없는 경우
        if data["type"] == "withoutAudio":
            form_object = Form.objects.get(id=data["formId"])

            # 기본 튜닝
            self.default_tuning()

            # 대화 계속하기
            self.continue_conversation(form_object)

        # 오디오 파일이 있는 경우
        elif data["type"] == "withAudio":
            # base64 디코딩
            audio_blob = data["audioBlob"]
            audio_data = base64.b64decode(audio_blob)

            # 오디오 파일로 변환
            audio_file = ContentFile(audio_data)
            
            file_url = get_file_url(audio_file, uuid)

            # tempfile : 임시 파일 생성하는 파이썬 라이브러리
            # NamedTemporaryFile() : 임시 파일 객체 반환
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_file_path = temp_file.name

            with open(temp_file_path, "wb") as file:
                # audio_file을 chunks() 메서드를 통해 블록 단위로 데이터를 읽어와서 file(temp_file_path)에 기록
                for chunk in audio_file.chunks():
                    file.write(chunk)

            # 블록 단위의 음성 파일을 저장하고 있는 temp_file_path을 whisper API로 텍스트로 변환
            with open(temp_file_path, "rb") as audio_file:
                transcript = openai.Audio.transcribe("whisper-1", audio_file)

            transcription = transcript["text"]

            # Question 테이블의 마지막 Row 가져오기
            last_row = Question.objects.latest("question_id")

            # 답변 테이블에 추가
            Answer.objects.create(content=transcription, question_id=last_row, recode_file=file_url)
            answer_object = Answer.objects.latest("answer_id")
            print(transcription)

            # formId를 통해서 question 테이블을 가져옴
            form_object = Form.objects.get(id=data["formId"])
            questions = form_object.questions.all()

            self.default_tuning()

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
        elif data["type"] == "noReply":
            print("noReply")
            # base64 디코딩
            audio_blob = data["audioBlob"]
            audio_data = base64.b64decode(audio_blob)

            # 오디오 파일로 변환
            audio_file = ContentFile(audio_data)

            # 파일 업로드 및 URL 받아오기
            file_url = get_file_url(audio_file, uuid)

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
            last_row = Question.objects.latest("question_id")

            # 답변 테이블에 추가
            Answer.objects.create(content=transcription, question_id=last_row, recode_file=file_url)
            self.send(json.dumps({"last_topic_answer":"last"}))
            print("send Data")

        else:
            self.question_number = data["questionNum"]

    # 질문과 대답 추가
    def add_question_answer(self, question, answer):
        existing_content = self.conversation[0]["content"]  # 기존 content 가져오기
        new_content = existing_content + " Q. " + question + " A. " + answer
        self.conversation[0]["content"] = new_content

    def continue_conversation(self, form_object):
        messages = ""
        # stream으로 메시지 받아오는 반복문
        for chunk in openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.conversation,
            temperature=0.7,
            stream=True,
        ):
            # 파이썬은 들여쓰기로 블록을 설정할 수 있음. 따라서, 아래 코드들 모두 for문 안에 속한 것임
            # 메시지 처리가 완료되었는지 확인
            finish_reason = chunk.choices[0].finish_reason
            # stop일 경우 대화가 끝났으니깐 send()로 WebSocket을 통해 Client에게 빈 메시지 전송하고 for 반복문 탈출
            if chunk.choices[0].finish_reason == "stop":
                self.send(json.dumps({"message": "", "finish_reason": finish_reason}))
                break
            # gpt가 생성한 메시지를 message에 저장
            message = chunk.choices[0].delta["content"]
            messages += message
            # 메시지를 클라이언트로 바로 전송
            self.send(json.dumps({"message": message, "finish_reason": finish_reason}))

        Question.objects.create(content=messages, form_id=form_object)

    # 기본 면접 기본 튜닝
    def default_tuning(self):
        # 대화 시작 메시지 추가
        self.conversation.append(
            {
                "role": "system",
                "content": "You're a interviewer. You don't make any unnecessary expressions asides from giving interview questions.",
            }
        )
        self.conversation.append(
            {
                "role": "user",
                "content": 'function_name: [basic_interview] input: ["number_of_questions"] rule: [I want you to act as a interviewer, asking basic questions for the interviewee.\
                        Ask me the number of "number_of_questions".\
                        Your task is to simply make common basic questions and provide questions to me.\
                        Do not ask me questions about jobs.\
                        Do not ask the same question or similar question more than once\
                        You should create total of "number_of_questions" amount of questions, and provide it once at a time.\
                        You should ask the next question only after I have answered to the question.\
                        Do not include any explanations or additional information in your response, simply provide the generated question.\
                        You should also provide only one question at a time.\
                        As shown in the example below, please ask basic questions in all fields regardless of occupation or job.\
                        Do not ask questions related to my answer, ask me a separate basic question like the example below\
                        Example questions would be questions such as "What motivated you to apply for our company?", "Talk about your strengths and weaknesses."\
                        Keep in mind that these are the basic questions that you ask in an interview regardless of your occupation\
                        Let me know this is the last question.\
                        You must speak only in Korean during the interview.] personality_interview("5")',
            }
        )
