from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from drf_yasg.utils import swagger_auto_schema
from dotenv import load_dotenv
import openai
import base64

from forms.models import Form
from .tasks import process_whisper_data
from django.core.files.base import ContentFile
from .models import Answer, Question
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

load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")

# 기본 인터뷰
class DefaultInterview(APIView):
    parser_classes = [MultiPartParser]

    # 답변과 상관없이 질문을 랜덤으로 뽑아서 지원자에게 질문
    @swagger_auto_schema(
        operation_description="심층 면접 데이터 최초 받기",
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
        # 랜덤으로 기본 질문 1개 뽑기
        message = self.pick_random_question()

        # form_id 받기, 파라미터로 받기
        form_id = request.GET.get("form_id")

        # form_id에 해당하는 Form 객체 생성
        form_object = Form.objects.get(id=form_id)

        # Question 테이블에 Form 객체 데이터 추가
        # form_id=form_object : Question의 외래키를 추가하여 연결시킴
        Question.objects.create(content=message, form_id=form_object)

        return Response(message, status=status.HTTP_200_OK)

    # 음성 데이터를 받아야 하는 경우
    @swagger_auto_schema(
        # API 작업에 대한 설명
        operation_description="음성 데이터 POST",
        # 작업의 고유 식별자
        operation_id="음성 파일을 업로드 해주세요.",
        # voice_file 파일을 업로드하는 매개변수를 정의
        manual_parameters=[
            openapi.Parameter(
                name="form_id",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                required=True,
                description="지원 정보 아이디",
            ),
            openapi.Parameter(
                name="question_id",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                required=True,
                description="질문 아이디",
            ),
            openapi.Parameter(
                name="voice_file",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="음성 데이터",
            ),
        ],
        # API 응답에 대한 설명
        responses={400: "Invalid data in uploaded file", 200: "Success"},
    )
    # @action : Django ViewSet에서 사용되며, 특정 작업에 대한 추가적인 액션을 정의할 때 사용
    @action(
        detail=False,
        methods=["post"],
        parser_classes=(MultiPartParser,),
        name="upload-voice-file",
        url_path="upload-voice-file",
    )
    def post(self, request, format=None):
        self.conversation = []

        # 음성 답변 받기
        audio_file = request.FILES["voice_file"]
        form_id = request.data["form_id"]
        question_id = request.data["question_id"]
        # 음성 -> 텍스트
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        transcription = transcript["text"]

        #
        question_object = Question.objects.get(question_id=question_id)
        # Answer.content에 답변 저장
        Answer.objects.create(content=transcription, question_id=question_object)

        # 랜덤으로 질문 1개 뽑기
        message = self.pick_random_question()

        # id=form_id인 Form 객체 가져오기(get)
        form_object = Form.objects.get(id=form_id)

        Question.objects.create(content=message, form_id=form_object)

        # Answer.objects.create(content=transcription, question_id=question_id, recode_file='s3_주소')

        # Response객체를 생성하여 데이터와 상태 코드 반환
        return Response(transcription, status=status.HTTP_200_OK)

    # 질문을 랜덤으로 뽑는 함수
    def pick_random_question(self):
        # 중복 질문이 나오면 다시 뽑음 (그냥 삭제하는 걸로 할까?)
        pick_question = []
        while True:
            basic_questions_list = [
                "우리 회사에 지원한 동기가 무엇입니까?",
                "자신의 장점과 단점에 대해 이야기해보세요.",
                "최근에 읽은 책이나 영화는 무엇입니까?",
                "본인의 취미나 특기가 무엇입니까?",
                "자신만에 스트레스 해소법은 무엇입니까?",
                "5년 뒤, 10년 뒤 자신의 모습이 어떨 것 같습니까?",
                "가장 존경하는 인물은 누구입니까?",
                "본인이 추구하는 가치나 생활신조, 인생관, 좌우명은 무엇입니까?",
                "자기 계발을 위해 무엇을 합니까?",
                "취업기간에 무엇을 하셨나요?",
                "가장 기억에 남는 갈등 경험을 말해주세요",
                "가장 필요한 역량은 무엇이라 생각하나요?",
                "우리 회사의 단점이 무엇이라고 생각하나요?",
                "성취를 이룬 경험이 있나요? 그 경험을 설명해주세요.",
                "과거에 어떤 도전적인 상황을 겪었으며, 그 상황에서 어떻게 대응했나요?",
            ]

            message = random.choice(basic_questions_list)

            if message in pick_question:
                continue

            pick_question.append(message)
            break

        return message


# 상황 부여 면접
class SituationInterview(APIView):
    # 처음 데이터를 받아야 하는 경우 -> 음성 데이터는 없음. 그냥 GPT 질문 시작.
    @swagger_auto_schema(responses={"200": ResponseVoiceSerializer})
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
        self.conversation.append({"role": "assistant", "content": "ok. i understand."})
        self.conversation.append(
            {
                "role": "user",
                "content": "Create appropriate situational interview questions based on the position of front-end developer. Ask one question at a time. Don't even say yes, just ask questions.",
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

        message = completion.choices[0].message["content"]
        return message


# 심층 면접 인터뷰
class DeepInterview(APIView):
    conversation = []

    # 처음 데이터를 받아야 하는 경우 -> 음성 데이터는 없음. 그냥 GPT 질문 시작.
    @swagger_auto_schema(
        operation_description="심층 면접 데이터 최초 받기",
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
        # Question 테이블에 데이터 추가, form Object 얻기
        form_object = Form.objects.get(id=form_id)

        # 기본 튜닝
        self.default_tuning(
            form_object.sector_name,
            form_object.job_name,
            form_object.career,
            form_object.resume,
        )

        # 대화 계속하기
        message = self.continue_conversation()

        Question.objects.create(content=message, form_id=form_object)

        return Response(message, status=status.HTTP_200_OK)

    # 음성 데이터를 받아야 하는 경우

    @swagger_auto_schema(
        operation_description="음성 데이터 POST",
        operation_id="음성 파일을 업로드 해주세요.",
        manual_parameters=[
            openapi.Parameter(
                name="form_id",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                required=True,
                description="지원 정보 아이디",
            ),
            openapi.Parameter(
                name="question_id",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                required=True,
                description="질문 아이디",
            ),
            openapi.Parameter(
                name="voice_file",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="음성 데이터",
            ),
        ],
        responses={400: "Invalid data in uploaded file", 200: "Success"},
    )
    @action(
        detail=False,
        methods=["post"],
        parser_classes=(MultiPartParser,),
        name="upload-voice-file",
        url_path="upload-voice-file",
    )
    def post(self, request, format=None):
        # 답변을 받고, 응답을 해주는 부분 -> 음성 파일 추출 필요
        # 오디오 파일, 지원 정보 아이디, 질문 아이디를 Request Body로 받음
        self.conversation = []
        audio_file = request.FILES["voice_file"]
        form_id = request.data["form_id"]
        question_id = request.data["question_id"]
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        transcription = transcript["text"]

        # S3에 업로드하는 로직 필요!

        # 답변 테이블에 추가
        question_object = Question.objects.get(question_id=question_id)
        Answer.objects.create(content=transcription, question_id=question_object)

        form_object = Form.objects.get(id=form_id)
        questions = form_object.questions.all()

        # 기본 튜닝
        self.default_tuning(
            form_object.sector_name,
            form_object.job_name,
            form_object.career,
            form_object.resume,
        )

        try:
            # 질문, 대답 추가.
            for question in questions:
                answer = question.answer
                self.add_question_answer(question.content, answer.content)
        except:
            error_message = "같은 지원 양식의 question 테이블과 answer 테이블의 갯수가 일치하지 않습니다."
            response = HttpResponse(error_message, status=500)
            return response

        message = self.continue_conversation()

        # 질문 테이블에 정보 추가
        Question.objects.create(content=message, form_id=form_object)

        return Response(message, status=status.HTTP_200_OK)

    # 질문과 대답 추가
    def add_question_answer(self, question, answer):
        self.conversation.append({"role": "assistant", "content": question})
        self.conversation.append({"role": "assistant", "content": answer})

    def continue_conversation(self):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=self.conversation, temperature=0.9, n=1
        )

        message = completion.choices[0].message["content"]
        return message

    # 기본 튜닝
    def default_tuning(self, seletor_name, job_name, career, resume):
        # 대화 시작 메시지 추가
        self.conversation.append(
            {
                "role": "user",
                "content": "You're an interviewer. When I ask you to 'give me a question', then start asking question.",
            }
        )

        self.conversation.append(
            {"role": "assistant", "content": "sure. i understand."}
        )

        self.conversation.append(
            {
                "role": "user",
                "content": "ask only one question at a time in the chat. and ask another question after I provided the answer",
            }
        )

        self.conversation.append(
            {"role": "assistant", "content": "sure. i understand."}
        )
        self.conversation.append(
            {
                "role": "user",
                "content": "Don't give me an explanation, a summary, or an appreciation of my answer, you just have to ask me question",
            }
        )

        self.conversation.append(
            {"role": "assistant", "content": "sure. i understand."}
        )

        # 내용 추가
        self.conversation.append(
            {
                "role": "user",
                "content": "I will apply to "
                + seletor_name
                + " as a "
                + job_name
                + ". Also, I am a"
                + career
                + " "
                + job_name
                + " applicant.",
            },
        )
        self.conversation.append(
            {"role": "assistant", "content": "sure. i understand."}
        )

        self.conversation.append(
            {
                "role": "user",
                "content": "From now on, I will give you a total of three self-introductions. I'll give you one every time I ask a question. Remember each self-introduction and answer 'I understand'. Also, don't ask questions while giving the content.",
            },
        )
        self.conversation.append(
            {
                "role": "assistant",
                "content": "sure. i understand. please proceed with your self-introduction.",
            }
        )

        self.conversation.append(
            {
                "role": "user",
                "content": "Please describe any of your experiences so far that you are confident of achieving innovation. 'First challenge in front-end web development' I became interested in technology stacks in front-end web development that I had never encountered when I was undergraduate, and I studied by making projects personally during the second semester from the summer vacation of the fourth grade. I learned HTML and CSS natively and then created a project that uses the JavaScript framework. We selected React and Vue as representative JavaScript frameworks and created 'shopping mall site' and 'movie information search site', respectively. Although there are no objective figures or indicators to prove performance, I was confident that I had increased my web development capabilities in that I had created websites that functioned with technology actually used in my work. In the process of implementing a 'shopping mall site' using React, the components that make up the screen were not difficult to design and style, but there were difficulties in implementing the function of adding and removing products to the shopping cart. The process of using multiple hooks and contexts provided by React, such as useState, useCallback, and useMemo, was unfamiliar and took a long time to implement the function. The 'Movie Information Search Site' linked the movie search API and was the first website to be developed using the API. I used the OMDB API key for API linkage, but there is still a problem that the OMDB API key is exposed on the code, but I thought I became more familiar with Vue by making it using Vue router, bootstrap, and Vue for status management.",
            },
        )
        self.conversation.append(
            {
                "role": "assistant",
                "content": "i understand. please proceed with your self-introduction.",
            }
        )
        self.conversation.append(
            {
                "role": "user",
                "content": "Please indicate your discriminatory strengths in the job you want to apply for.'Communication skills and collaboration skills' Developers believe that collaboration is essential. In fact, if you work at the front end, you will basically communicate with planners, designers, and backend developers, but if you don't have full knowledge of development, I think there will be problems communicating in developmental languages. I studied computer science and theoretical knowledge thoroughly when I was an undergraduate, and most of my major subjects got 'A+' or 'A'. Working on team projects with this complete theoretical knowledge, I was able to choose terms that were as easy as possible to communicate and communicate with the other person easily. Thanks to this, there was no misunderstanding between members due to communication problems in the process of carrying out most team projects. If you do actual work, you may have technical communication or you may not understand it well in the process, but I will make sure that there is no problem with communication by asking politely again with activeness. In addition, I think 'activity' and 'grit' are also important for collaboration ability. When I was working on various team projects during my undergraduate years, including graduation projects, I always tried to find a solution when I encountered something I didn't know while playing my role. When I couldn't solve it, I used to ask politely with 'activity.' I think my 'activity' and 'grit' will motivate the members to collaborate.",
            },
        )
        self.conversation.append(
            {
                "role": "assistant",
                "content": "i understand. please proceed with your third self-introduction.",
            }
        )

        self.conversation.append(
            {
                "role": "user",
                "content": "If you join the company, please describe the vision you dream of. The front-end development job is to develop everything the customer sees. In other words, I think it is making the first impression of Carrot Insurance because it is in charge of the first part that the customer sees. I find this work very attractive and I want to be a key member who can contribute to the development team that sees and reflects customer responses immediately. Devices and browsers are becoming more and more diverse, and in order to provide customers with a web environment that fits them, as a front-end developer, I will act as a reliable bridge between customers and Carrot Insurance. The front-end development sector is trending faster than other sectors. To keep up with this, I will try to learn new technologies and trends steadily without continuing to settle for one skill. We will always strive to implement the user interface and user experience technically and accurately through continuous learning, and we will think from your perspective. I think the expansion of online business will be more severe in the future. As a result, customers will be increasingly exposed to online websites, and I believe that the front-end development job has a vision. For me, who loves to learn and learn new skills, I am confident that Carrot Insurance's front-end development job is the best place to grow together with the competence. start interview",
            }
        )

        self.conversation.append(
            {
                "role": "assistant",
                "content": "Thank you for providing your self-introductions.",
            }
        )

        self.conversation.append(
            {
                "role": "user",
                "content": "Now you extract the above self-introduction specifically. Ask a famous and tricky question based on the this extraction. You don't have to show me the extract, just ask me question. and re-extract and ask question when you're done with the tail-biting method. and you must say only korean. and Don't say anything other than a question from now on. give me a question.",
            }
        )


# 성향(인성) 면접 인터뷰
class PersonalityInterview(APIView):
    conversation = []

    # 처음 데이터를 받아야 하는 경우 -> 음성 데이터는 없음. 그냥 GPT 질문 시작.
    @swagger_auto_schema(
        operation_description="심층 면접 데이터 최초 받기",
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
        # 기본 튜닝
        self.default_tuning()

        # 대화 계속하기
        message = self.continue_conversation()

        # form_id 받기, 파라미터로 받기
        form_id = request.GET.get("form_id")

        # Question 테이블에 데이터 추가, form Object 얻기
        form_object = Form.objects.get(id=form_id)

        Question.objects.create(content=message, form_id=form_object)


        return Response(message, status=status.HTTP_200_OK)


        # 음성 데이터를 받아야 하는 경우
    @swagger_auto_schema(
        operation_description="음성 데이터 POST",
        operation_id="음성 파일을 업로드 해주세요.",
        manual_parameters=[
            openapi.Parameter(
                name="form_id",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                required=True,
                description="지원 정보 아이디",
            ),
            openapi.Parameter(
                name="question_id",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                required=True,
                description="질문 아이디",
            ),
            openapi.Parameter(
                name="voice_file",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="음성 데이터",
            ),
        ],
        responses={400: "Invalid data in uploaded file", 200: "Success"},
    )
    @action(
        detail=False,
        methods=["post"],
        parser_classes=(MultiPartParser,),
        name="upload-voice-file",
        url_path="upload-voice-file",
    )
    def post(self, request, format=None):
        # 답변을 받고, 응답을 해주는 부분 -> 음성 파일 추출 필요
        # 오디오 파일, 지원 정보 아이디, 질문 아이디를 Request Body로 받음
        audio_file = request.FILES["voice_file"]
        form_id = request.data["form_id"]
        question_id = request.data["question_id"]
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        transcription = transcript["text"]

        # S3에 업로드하는 로직 필요!

        # 답변 테이블에 추가
        question_object = Question.objects.get(question_id=question_id)
        Answer.objects.create(content=transcription, question_id=question_object)

        form_info = Form.objects.get(id=form_id)
        questions = form_info.questions.all()

        # 기본 튜닝
        self.default_tuning()

        print(questions)
        # 질문, 대답 추가.
        for question in questions:
            answer = question.answer
            self.add_question_answer(question.content, answer.content)

        message = self.continue_conversation()

        # 질문 테이블에 정보 추가
        Question.objects.create(content=message, form_id=form_info)

        return Response(message, status=status.HTTP_200_OK)


    # 인성 면접 기본 튜닝
    def default_tuning(self):
            # 대화 시작 메시지 추가
        self.conversation.append(
            {
                "role": "user",
                "content": "You're an interviewer. When I ask you to 'start interview', then start asking question.",
            }
        )
        self.conversation.append(
            {"role": "assistant", "content": "sure. i understand."}
        )
        self.conversation.append(
            {
                "role": "user",
                "content": "ask only one question at a time in the chat. and ask another question after I provided the answer",
            }
        )
        self.conversation.append(
            {"role": "assistant", "content": "sure. i understand."}
        )
        self.conversation.append(
            {
                "role": "user",
                "content": "Don't give me an explanation, a summary, or an appreciation of my answer, you just have to ask me question",
            }
        )
        self.conversation.append(
            {"role": "assistant", "content": "sure. i understand."}
        )
        self.conversation.append(
            {
                "role": "user",
                "content": "You must prepare 3 common personality interview questions.",
            }
        )
        self.conversation.append(
            {"role": "assistant", "content": "sure. i understand."}
        )

        self.conversation.append(
            {
                "role": "user",
                "content": "From now, I will give you some personality interview questions."
            }
        )
        self.conversation.append(
            {"role": "assistant", "content": "Ok."}
        )

        self.conversation.append(
            {
                "role": "user",
                "content": "Do you prefer working in a team or on your own? If you could change one thing about your personality, what would it be and why?"
            }
        )
        self.conversation.append(
            {"role": "assistant", "content": "Ok. I understand."}
        )

        self.conversation.append(
            {
                "role": "user",
                "content": "How do you handle stress and pressure? What motivates you? If you could change one thing about your personality, what would it be and why? What are you passionate about"
            }
        )
        self.conversation.append(
            {"role": "assistant", "content": "Ok. I understand."}
        )

        self.conversation.append(
            {
                "role": "user",
                "content": "You must randomly extract those examples to use them on interview. You should also make up your own questions based on those questions.",
            }
        )
        self.conversation.append(
            {"role": "assistant", "content": "ok. i understand."}
        )

        self.conversation.append(
            {
                "role": "user",
                "content": "When I say 'start interview', you should start giving me questions. Ask only in Korean. Don't ever talk in English when the interview starts.",
            }
        )
        self.conversation.append(
            {"role": "assistant", "content": "sure. i understand."}
        )
        self.conversation.append(
            {
                "role": "user",
                "content": "start interview.",
            }
        )


    # 질문과 대답 추가
    def add_question_answer(self, question, answer):
        self.conversation.append({"role": "assistant", "content": question})
        self.conversation.append({"role": "assistant", "content": answer})

    def continue_conversation(self):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=self.conversation, temperature=0.9, n=1
        )

        message = completion.choices[0].message["content"]
        return message
