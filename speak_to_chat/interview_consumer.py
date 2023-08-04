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
import random
import time

from forms.models import Qes_Num

load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")


class InterviewConsumer(WebsocketConsumer):

    def connect(self):
        self.accept()
        # 대화 기록을 저장할 리스트
        self.conversation = []
        self.default_transcriptions = []
        self.situation_transcriptions = []
        self.personal_transcriptions = []
        
        self.default_last_questions = []
        self.situation_last_questions = []
        self.personal_last_questions = []
        
        self.default_audio_file_urls = []
        self.situation_audio_file_urls = []
        self.personal_audio_file_urls = []

    def disconnect(self, closed_code):
        form_object = Form.objects.get(id=self.form_id)
        # 만약에 중간에 끊킨 경우, form_id와 관련된 것 전부 삭제
        questions = Question.objects.filter(form_id=form_object)
        question_numbers = questions.count()
        
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

        # 초기 질문 갯수 세팅
        if data["type"] == "initialSetting":
            # 전체 질문 수
            self.question_number = data["questionNum"]
            self.default_question_num = data["defaultQuestionNum"]
            self.situation_question_num = data["situationQuestionNum"]
            self.deep_question_num = data["deepQuestionNum"]
            self.personality_question_num = data["personalityQuestionNum"]
            self.form_id = data["formId"]

            # 이전 면접에서 저장되었던 질문 수
            form_object = Form.objects.get(id=data["formId"])
            questions = form_object.questions.all()
            self.before_qes = questions.count()

            Qes_Num.objects.create(
                total_que_num=self.question_number,
                default_que_num=self.default_question_num,
                situation_que_num=self.situation_question_num,
                deep_que_num=self.deep_question_num,
                personality_que_num=self.personality_question_num,
                form_id=form_object,
            )

        else:
            self.interview_type = data["interviewType"]

            # 기본 면접인 경우
            if self.interview_type == "default":
                print("기본 면접의 경우")

                # 오디오 파일이 없는 경우
                if data["type"] == "withoutAudio":
                    form_object = Form.objects.get(id=data["formId"])
                    
                    # 가장 처음 할 질문
                    first_question = "1분 자기소개를 해주세요."
                    
                    # 최초 기본 면접 질문
                    self.default_conversation(form_object, first_question)

                # 오디오 파일이 있는 경우
                elif data["type"] == "withAudio":

                    # base64 디코딩
                    audio_blob = data["audioBlob"]
                    audio_data = base64.b64decode(audio_blob)

                    # 오디오 파일로 변환
                    audio_file = ContentFile(audio_data)
                    
                    audio_file_url = get_file_url("audio", audio_file)
                    self.default_audio_file_urls.append(audio_file_url)

                    # celery에 temp_file_path 전달해서 get()을 통해 동기적으로 실행(결과가 올 때까지 기다림)
                    self.default_transcriptions.append(process_whisper_data.delay(audio_file_url))

                    # Question 테이블의 마지막 Row 가져오기
                    last_row_per_form = Form.objects.get(id=self.form_id).questions.last()
                    self.default_last_questions.append(last_row_per_form)

                    # formId를 통해서 question 테이블을 가져옴
                    form_object = Form.objects.get(id=data["formId"])
                    questions = form_object.questions.all().order_by('question_id')

                    # 기존 questions 데이터를 슬라이싱하여 새롭게 생성된 questions만 가져옴
                    questions_included = questions[self.before_qes:]

                    for question in questions_included:
                        self.add_question_answer(question.content)
                    
                    # 랜덤으로 질문 뽑기
                    pick_question = self.pick_random_question()
                    
                    # 뽑은 질문을 client에게 보내기
                    self.default_conversation(form_object, pick_question)

                
                # 대답만 추가하는 경우
                elif data["type"] == "noReply":
                    print("noReply")

                    # base64 디코딩
                    audio_blob = data["audioBlob"]
                    audio_data = base64.b64decode(audio_blob)

                    # 오디오 파일로 변환
                    audio_file = ContentFile(audio_data)

                    # 파일 업로드 및 URL 받아오기
                    audio_file_url = get_file_url("audio", audio_file)
                    self.default_audio_file_urls.append(audio_file_url)

                    # celery에 temp_file_path 전달해서 get()을 통해 동기적으로 실행(결과가 올 때까지 기다림)
                    self.default_transcriptions.append(process_whisper_data.delay(audio_file_url))

                    # Question 테이블의 마지막 Row 가져오기
                    last_row_per_form = Form.objects.get(id=self.form_id).questions.last()
                    self.default_last_questions.append(last_row_per_form)
                    

                    form_object = Form.objects.get(id=self.form_id)
                    questions = Question.objects.filter(form_id=form_object)
                    if self.question_number == questions.count():
                        self.add_answer_data()
                    
                    self.send(json.dumps({"last_topic_answer":"default_last"}))
                    


                    # 이전 질문 개수에 기본면접 질문 개수 더하여 저장
                    self.before_qes += self.default_question_num

            else:
                pass

            # 상황 면접인 경우
            if self.interview_type == "situation":
                print("상황 면접의 경우")

                # 오디오 파일이 없는 경우
                if data["type"] == "withoutAudio":
                    form_object = Form.objects.get(id=data["formId"])
                    
                    # 기본 튜닝
                    self.situation_interview_tuning(
                        form_object.sector_name,
                        form_object.job_name,
                        form_object.career,
                    )

                    # 대화 계속하기
                    self.continue_conversation(form_object)
                    
                elif data["type"] == "withAudio":
                    # # base64 디코딩
                    audio_blob = data["audioBlob"]
                    audio_data = base64.b64decode(audio_blob)

                    # 오디오 파일로 변환
                    audio_file = ContentFile(audio_data)

                    # 파일 업로드 및 URL 받아오기
                    audio_file_url = get_file_url("audio", audio_file)
                    self.situation_audio_file_urls.append(audio_file_url)

                    # celery에 temp_file_path 전달해서 get()을 통해 동기적으로 실행(결과가 올 때까지 기다림)
                    self.situation_transcriptions.append(process_whisper_data.delay(audio_file_url))

                    # Question 테이블의 마지막 Row 가져오기
                    last_row_per_form = Form.objects.get(id=self.form_id).questions.last()
                    self.situation_last_questions.append(last_row_per_form)

                    # formId를 통해서 question 테이블을 가져옴
                    form_object = Form.objects.get(id=data["formId"])
                    questions = form_object.questions.all().order_by('question_id')

                    # 기존 questions 데이터를 슬라이싱하여 새롭게 생성된 questions만 가져옴
                    questions_included = questions[self.before_qes:]

                    self.situation_interview_tuning(
                        form_object.sector_name,
                        form_object.job_name,
                        form_object.career,
                    )

                    for question in questions_included:
                        self.add_question_answer(question.content)

                    self.continue_conversation(form_object)
                    
                elif data["type"] == "noReply":
                    # base64 디코딩
                    audio_blob = data["audioBlob"]
                    audio_data = base64.b64decode(audio_blob)

                    # 오디오 파일로 변환
                    audio_file = ContentFile(audio_data)

                    # 파일 업로드 및 URL 받아오기
                    audio_file_url = get_file_url("audio", audio_file)
                    self.situation_audio_file_urls.append(audio_file_url)

                    # celery에 temp_file_path 전달해서 get()을 통해 동기적으로 실행(결과가 올 때까지 기다림)
                    self.situation_transcriptions.append(process_whisper_data.delay(audio_file_url))

                    # Question 테이블의 마지막 Row 가져오기
                    last_row_per_form = Form.objects.get(id=self.form_id).questions.last()
                    self.situation_last_questions.append(last_row_per_form)
                    
                    form_object = Form.objects.get(id=self.form_id)
                    questions = Question.objects.filter(form_id=form_object)
                    if self.question_number == questions.count():
                        print("상황")
                        self.add_answer_data()
                        
                    self.send(json.dumps({"last_topic_answer":"situation_last"}))
                    
                    # 이전 질문 개수에 상황면접 질문 개수 누적
                    self.before_qes += self.situation_question_num

            else:
                pass

            # 심층 면접인 경우
            if self.interview_type == "deep":
                print("심층 면접의 경우")
                # 오디오 파일이 없는 경우
                if data["type"] == "withoutAudio":
                    form_object = Form.objects.get(id=data["formId"])
                    # 기본 튜닝
                    self.deep_interview_tuning(
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

                    # 파일 업로드 및 URL 받아오기
                    audio_file_url = get_file_url("audio", audio_file)

                    # celery에 temp_file_path 전달해서 get()을 통해 동기적으로 실행(결과가 올 때까지 기다림)
                    transcription = process_whisper_data.delay(audio_file_url).get()

                    # Question 테이블의 마지막 Row 가져오기
                    last_row_per_form = Form.objects.get(id=self.form_id).questions.last()

                    # 답변 테이블에 추가
                    Answer.objects.create(content=transcription, question_id=last_row_per_form, recode_file=audio_file_url)

                    # formId를 통해서 question 테이블을 가져옴
                    form_object = Form.objects.get(id=data["formId"])
                    questions = form_object.questions.all().order_by('question_id')

                    # 기존 questions 데이터를 슬라이싱하여 새롭게 생성된 questions만 가져옴
                    questions_included = questions[self.before_qes:]

                    self.deep_interview_tuning(
                        form_object.sector_name,
                        form_object.job_name,
                        form_object.career,
                        form_object.resume,
                    )

                    # question 테이블에서 질문과 답변에 대해 튜닝 과정에 추가함.
                    try:
                        for question in questions_included:
                            answer = question.answer
                            self.add_question_answer(question.content, answer.content)
                    except:
                        error_message = "같은 지원 양식의 question 테이블과 answer 테이블의 갯수가 일치하지 않습니다."
                        print(error_message)

                    self.continue_conversation(form_object)


                # 대답만 추가하는 경우
                elif data["type"] == "noReply":
                    # base64 디코딩
                    audio_blob = data["audioBlob"]
                    audio_data = base64.b64decode(audio_blob)

                    # 오디오 파일로 변환
                    audio_file = ContentFile(audio_data)

                    # 파일 업로드 및 URL 받아오기
                    audio_file_url = get_file_url("audio", audio_file)

                    # celery에 s3_url 전달해서 get()을 통해 동기적으로 실행(결과가 올 때까지 기다림)
                    transcription = process_whisper_data.delay(audio_file_url).get()

                    # Question 테이블의 마지막 Row 가져오기
                    last_row_per_form = Form.objects.get(id=self.form_id).questions.last()
                    
                    # 답변 테이블에 추가
                    Answer.objects.create(content=transcription, question_id=last_question, recode_file=audio_file_url)
                    form_object = Form.objects.get(id=self.form_id)
                    questions = Question.objects.filter(form_id=form_object)
                    if self.question_number == questions.count():
                        self.add_answer_data()
                    self.send(json.dumps({"last_topic_answer":"deep_last"}))

                    # 이전 질문 개수에 심층면접 질문 개수 누적
                    self.before_qes += self.deep_question_num

            else:
                pass 

            # 성향 면접인 경우
            if self.interview_type == "personality":
                print("성향 면접의 경우")
                # 오디오 파일이 없는 경우
                if data["type"] == "withoutAudio":
                    form_object = Form.objects.get(id=data["formId"])

                    # 기본 튜닝
                    self.personal_interview_tuning()

                    # 대화 계속하기
                    self.continue_conversation(form_object)
                    
                elif data["type"] == "withAudio":
                    # base64 디코딩
                    audio_blob = data["audioBlob"]
                    audio_data = base64.b64decode(audio_blob)

                    # 오디오 파일로 변환
                    audio_file = ContentFile(audio_data)

                    # 파일 업로드 및 URL 받아오기
                    audio_file_url = get_file_url("audio", audio_file)
                    self.personal_audio_file_urls.append(audio_file_url)

                    # celery에 temp_file_path 전달해서 get()을 통해 동기적으로 실행(결과가 올 때까지 기다림)
                    self.personal_transcriptions.append(process_whisper_data.delay(audio_file_url))

                    # Question 테이블의 마지막 Row 가져오기
                    last_row_per_form = Form.objects.get(id=self.form_id).questions.last()
                    self.personal_last_questions.append(last_row_per_form)
                    
                    # formId를 통해서 question 테이블을 가져옴
                    form_object = Form.objects.get(id=data["formId"])
                    questions = form_object.questions.all().order_by('question_id')

                    # 기존 questions 데이터를 슬라이싱하여 새롭게 생성된 questions만 가져옴
                    questions_included = questions[self.before_qes:]

                    self.personal_interview_tuning()

                    # question 테이블에서 질문과 답변에 대해 튜닝 과정에 추가함.
                    for question in questions_included:
                        self.add_question_answer(question.content)

                    self.continue_conversation(form_object)

                # 대답만 추가하는 경우
                elif data["type"] == "noReply":
                    # base64 디코딩
                    audio_blob = data["audioBlob"]
                    audio_data = base64.b64decode(audio_blob)

                    # 오디오 파일로 변환
                    audio_file = ContentFile(audio_data)

                    # 파일 업로드 및 URL 받아오기
                    audio_file_url = get_file_url("audio", audio_file)
                    self.personal_audio_file_urls.append(audio_file_url)

                    # celery에 temp_file_path 전달해서 get()을 통해 동기적으로 실행(결과가 올 때까지 기다림)
                    self.personal_transcriptions.append(process_whisper_data.delay(audio_file_url))

                    # Question 테이블의 마지막 Row 가져오기
                    last_row_per_form = Form.objects.get(id=self.form_id).questions.last()
                    self.personal_last_questions.append(last_row_per_form)
                    
                    form_object = Form.objects.get(id=self.form_id)
                    questions = Question.objects.filter(form_id=form_object)
                    if self.question_number == questions.count():
                        print("인성")
                        self.add_answer_data()
                    
                    self.send(json.dumps({"last_topic_answer":"personal_last"}))
                    

                    # 이전 질문 개수에 성향면접 질문 개수 누적
                    self.before_qes += self.personality_question_num
            else:
                pass
            
            
            form_object = Form.objects.get(id=self.form_id)
            questions = Question.objects.filter(form_id=form_object)
            last_question = questions.last()
            try:
                if (last_question.answer and self.question_number == questions.count()):
                    self.send(json.dumps({"last_topic_answer":"last"}))
            except:
                pass
            
        

    def add_answer_data(self):
        # 모든 작업이 완료될 때까지 기다림
        if len(self.default_transcriptions) > 0:
            for index, default_task_result in enumerate(self.default_transcriptions):
                # default_task_result에 대한 작업 수행
                default_transcription = default_task_result.get()
                # Answer 모델에 값을 저장
                Answer.objects.create(content=default_transcription, question_id=self.default_last_questions[index], recode_file=self.default_audio_file_urls[index])
                self.default_transcriptions = []
                
        if len(self.situation_transcriptions) > 0:
            for index, situation_task_result in enumerate(self.situation_transcriptions):
                # situation_task_result에 대한 작업 수행
                situation_transcription = situation_task_result.get()
                # Answer 모델에 값을 저장
                Answer.objects.create(content=situation_transcription, question_id=self.situation_last_questions[index], recode_file=self.situation_audio_file_urls[index])
                self.situation_transcriptions = []
                
        if len(self.personal_transcriptions) > 0:
            for index, personal_task_result in enumerate(self.personal_transcriptions):
                # personal_task_result에 대한 작업 수행
                personal_transcription = personal_task_result.get()
                # Answer 모델에 값을 저장
                Answer.objects.create(content=personal_transcription, question_id=self.personal_last_questions[index], recode_file=self.personal_audio_file_urls[index])
                self.personal_transcriptions = []

    # 질문과 대답 추가
    def add_question_answer(self, question, answer=None):
        self.conversation.append(
            {
                "role" : "assistant",
                "content": question
            }
        )
        # 심층면접의 경우
        if answer is not None:
            self.conversation.append(
                {
                    "role": "user",
                    "content": "'"+answer+"'"+" is my answer, and you give me a one question with a tail-to-tail in relation to my answer and job."
                }
            )
        else:
            self.conversation.append(
                {
                    "role": "user",
                    "content": "Another question, give me only one."
                }
            )


    def continue_conversation(self, form_object):
        messages = ""
        for chunk in openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.conversation,
            temperature=0.9,
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
        print(self.conversation)
        Question.objects.create(content=messages, form_id=form_object)
    
    # 기본 면접 한글자 단위로 보내기
    def default_conversation(self, form_object, question_content):
        messages = ""
        # question_content의 index와 원소를 순차적으로 반환하여 스트림 형식으로 출력
        for index, chunk in enumerate(question_content):
            is_last_char = ""
            # 현재 글자가 마지막 글자인지 확인
            if index == len(question_content) - 1:
                is_last_char = "stop"
            else:
                is_last_char = "incomplete"
                
            if is_last_char == "stop" :
                self.send(json.dumps({"message": chunk, "finish_reason": is_last_char}))
                break
            
            message = chunk
            messages += message

            # 메시지를 클라이언트로 바로 전송
            self.send(json.dumps({"message": message, "finish_reason": is_last_char}))
            
            time.sleep(0.05)

        Question.objects.create(content=messages, form_id=form_object)


    # 질문을 랜덤으로 뽑는 함수
    def pick_random_question(self):
        # 중복 질문이 나오면 다시 뽑음 (그냥 삭제하는 걸로 할까?)
        pick_question = []
        while True:
            basic_questions_list = [
                "자신의 인생에서 실패했던 경험을 이야기해보세요.",
                "인생에서 가장 열정적이었던 순간은 언제였나요?",
                "친구들은 당신을 어떤 사람이라고 말하나요?",
                "본인의 장점과 단점에 대해 이야기 해보세요.",
                "우리가 당신을 뽑아야 하는 이유는 무엇인가요?",
                "본인의 직업관은 무엇인가요?",
                "인생에 있어서 가장 기억에 남는 순간은 언제인가요?",
                "회사를 알게 된 계기가 무엇인가요?",
                "본인이 우리 회사에 어떤 도움을 줄 수 있을 것이라 생각하시나요?",
                "면접을 본 다른 기업이 있나요?",
                "회사 근무를 하면서 가장 중요하다고 생각하는 것이 무엇인가요?",
                "해당 직무에서 필요한 역량이 무엇이라 생각하시나요?",
                "우리 회사의 최근 이슈에 대해 찾아본 것이 있나요?",
                "회사의 인재상 중 어떤 점이 본인과 부합한다고 생각하시나요?",
                "고객이 불만사항을 제기하면 어떻게 대처하실껀가요?",
                "상사가 주말 근무, 야근을 지시한다면 어떻게 할 것인가요?",
                "해당 직무에서 필요한 자질 중 어떤 점이 부합 하다고 생각하시나요??",
                "직무와 관련하여 최근 관심 있는 이슈는 무엇인지 설명해 보세요",
                "취미 혹은 스트레스를 해소하는 방법은 무엇인가요?",
                "업무 하면서 가장 크게 실패했던 경험은 무엇인가요?",
                "추구하는 커리어의 목표는 무엇인가요?",
                "본인만의 업무 상 경쟁력은 무엇인가요?",
                "어떤 사람들과 일할 때 시너지가 나나요?",
                "회사에서 가장 힘들었던 경험은 무엇인가요?"
                "우리 회사에 지원한 동기가 무엇인가요?",
                "자신만에 스트레스 해소법은 무엇인가요?",
                "5년 뒤, 10년 뒤 자신의 모습이 어떨 것 같나요?",
                "가장 존경하는 인물을 말씀해주세요",
                "본인이 추구하는 가치나 생활신조, 인생관, 좌우명을 말씀해주세요",
                "자기 계발을 위해 무엇을 하시나요?",
                "취업기간에 무엇을 하셨나요?",
                "가장 기억에 남는 갈등 경험을 말해주세요",
                "가장 필요한 역량은 무엇이라 생각하나요?",
                "우리 회사의 단점이 무엇이라고 생각하나요?",
                "성취를 이룬 경험이 있나요? 그 경험을 설명해주세요.",
                ]

            question = random.choice(basic_questions_list)

            if question in pick_question:
                continue
            pick_question.append(question)
            break

        return question
        
    # 상황 면접 튜닝
    def situation_interview_tuning(self, selector_name, job_name, career):
        self.conversation = [
            {
                "role": "system",
                "content" : 'I am the person who wants to be a'+job_name+'and you are the interviewer. You ask me interview questions about specific situations that might arise while doing that job. Also, the content of the question should be specific and creative. and give me just one. Also, you, the interviewer, do not say anything outside of the question and use the word "지원자분" instead of "you". You just give an answer when it works, without explaining how it works and your role. Do not put formulas or descriptions such as "Interviewer:" and "Question:" before questions. Your answer is only in Korean.'
            },
        ]
    
    # 심층 면접 튜닝
    def deep_interview_tuning(self, selector_name, job_name, career, resume):
        self.conversation = [
            # {
            #     "role": "user",
            #     "content":'function_name: [interviewee_info] input: ["Company", "Job", "Career"] rule: [Please act as a skillful interviewer. We will provide the input form including "Company," "Professional," and "Career." Look at the sentences "Company," "Job," and "Career" to get information about me as an interview applicant. For example, let\'s say company = IT company, job = web front-end developer, experience = newcomer. Then you can recognize that you\'re a newbie applying to an IT company as a web front-end developer. And you can ask questions that fit this information. Also, you, the interviewer, do not say anything outside of the question and use the word "지원자분" instead of "you". You just give an answer when it works, without explaining how it works and your role. Do not put formulas or descriptions such as "Interviewer:" and "Question:" before questions. Your answer is only in Korean.]'
            #     # + 'function_name: [aggressive_position] rule: [Ask me questions in a tail-to-tail manner about what I answer. There may be technical questions about the answer, and there may be questions that you, as an interviewer, would dig into the answer.. For example, if the question asks, "What\'s your web framework?" the answer is, "It is React framework." So the new question is, "What do you use as a state management tool in React, and why do you need this?" It should be the same question. If you don\'t have any more questions, move on to the next topic.] '
            #     + 'function_name: [self_introduction] input : ["self-introduction"] rule: [We will provide an input form including a "self-introduction." Read this "self-introduction" and extract the content to generate a question. just ask one question. Don\'t ask too long questions. The question must have a definite purpose. and Just ask one question at a time.]'
            #     + 'interviewee_info(Company="'
            #     + selector_name
            #     + '", Job="'
            #     + job_name
            #     + '", Career="'
            #     + career
            #     + '")'
            #     + 'self_introduction("'
            #     + resume
            #     + '")',
            #     # + "aggressive_position()",
            # }
            # {
            #     "role": "system",
            #     "content": f"""You are the interviewer for {selector_name}. Your task is to generate questions based on the applicant's selector_name, job_name, career, and resume provided in the back. Generate questions that are tailored to the applicant's answers. Only one question should be generated at a time, and it should be in Korean. Use "applicant" instead of "you".
            #                 selector_name : {selector_name}
            #                 job_name : {job_name}
            #                 career : {career}
            #                 resume : {resume}"""
            # }
            # {
            #     "role": "system",
            #     "content": f"""You are the interviewer for {selector_name}. Also, you, the interviewer, do not say anything outside of the question and use the word "지원자분" instead of "you". You just give an answer when it works, without explaining how it works and your role. Do not put formulas or descriptions such as "Interviewer:" and "Question:" before questions. Generate up to five questions about the applicant\'s answers. When you move on to the next topic, don\'t say "Let\'s move on" and create a question right away. Don\'t summarize answers or self-introduction or generate understanding, just generate questions. Create only questions, not something like 1. 2. 3. and Question 1. Question 2. Question 3. . Your answer is only in Korean."""
            # },
            {
                "role": "system",
                "content":'function_name: [interviewee_info] input: ["Company", "Job", "Career"] rule: [We will provide the input form including "Company," "Job," and "Career." Look at the sentences "Company," "Job," and "Career" to get information about me as an interview applicant. For example, let\'s say company = IT company, job = web front-end developer, experience = newcomer. Then you can recognize that you\'re a newbie applying to an IT company as a web front-end developer. And you can ask questions that fit this information.]'
                + 'function_name: [self_introduction] input : ["self-introduction"] rule: [We will provide an input form including a "self-introduction." Read this "self-introduction" and extract the content to generate a question. just ask one question. Don\'t ask too long questions. The question must have a definite purpose. and Just ask one question at a time.]'
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
                + 'You just give an answer when it works, without explaining how it works and your role. Do not put formulas or descriptions such as "Interviewer:" and "Question:" before questions. Your answer is only in Korean. and give me just one question.'
            }
        ]
            
        # ]
        
    # 인성 면접 튜닝
    def personal_interview_tuning(self):
        self.conversation = [
            {
                "role": "system",
                "content" : 'You are a interviewer. Your task is to generate frequently asked personality interview questions that are similar to the sample questions you\'ll be asked in an interview. Don\'t say anything other than the question. Provide only one question at a time. Do not ever to not include any explanations or additional information in your response. Also, you, the interviewer, do not say anything outside of the question and use the word "지원자분" instead of "you". Do not put formulas or descriptions such as "Interviewer:" and "Question:" before questions. Separate "지원자분이" from "지원자분은" and use it in context. Generate Korean questions using natural grammar and context, especially grammatically correct postposition. Keep in mind - Don\'t ask the interviewee to introduce himself. Don\'t even greet the interviewee. example questions : What\'s the most important thing you look for in a friend?, Is there someone you look up to and why?, How do you handle the challenges of working on a team?, Do you think it\'s better to do what you love and what you\'re good at for a living? '
            },
        ]
