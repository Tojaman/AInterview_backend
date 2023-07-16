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
from .serializers import ResponseVoiceSerializer
from django.core.files.temp import NamedTemporaryFile
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import action
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from forms.models import Form
from .models import Question

load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")

# 기본 인터뷰
class DefaultInterview(APIView):
    parser_classes = [MultiPartParser]

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
                "content": "Start the interview. I will apply to Naver as a front-end developer. Also, Start the interview. I will apply to Naver as a front-end developer. Remember. I am applying for the first time in this field. ",
            },
        )

        self.conversation.append({"role": "assistant", "content": "ok. I understand."})

        self.conversation.append(
            {
                "role": "user",
                "content": "please ask me the questions one at a time. And answer only the question you created by translating them into Korean. Don't answer in English.",
            }
        )

        self.conversation.append({"role": "assistant", "content": "ok. I understand."})

        self.conversation.append(
            {
                "role": "user",
                "content": "Please prepare challenging and common question for interviewers when applying for Naver Front Developer.",
            }
        )

        # 대화 계속하기
        message = self.continue_conversation()

        return Response(message, status=status.HTTP_200_OK)

    # 음성 데이터를 받아야 하는 경우
    @swagger_auto_schema(
        operation_description="Upload container excel, if the columns and data are valid. Containers will be created. "
        "If container with such name already exists, it will be update instead",
        operation_id="Upload container excel",
        manual_parameters=[
            openapi.Parameter(
                name="voice_file",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="Document",
            )
        ],
        responses={400: "Invalid data in uploaded file", 200: "Success"},
    )
    @action(
        detail=False,
        methods=["post"],
        parser_classes=(MultiPartParser,),
        name="upload-excel",
        url_path="upload-excel",
    )
    def post(self, request, format=None):
        self.conversation = []

        # 답변을 받고, 응답을 해주는 부분 -> 음성 파일 추출 필요
        # 음성 파일을 추출하고, wav 파일로 저장 -> 오디오를 텍스트로 변환.
        audio_file = request.FILES["voice_file"]

        print(audio_file)
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        transcription = transcript["text"]

        # self.conversation.append(
        #     {
        #         "role": "user",
        #         "content": "Let's do a job interview simulation. You're an interviewer and I'm an applicant. When I ask you to start taking interview, then start asking questions. I will say the phrase “start the interview” for you to start. Ask one question at a time. Then, ask another question after I provided the answer. Continue this process until I ask you to stop. Please say 'Yes' if you understood my instructions.",
        #     }
        # )
        # self.conversation.append(
        #     {
        #         "role": "assistant",
        #         "content": "Yes. I am playing the role of the interviewer. I'll do my best.",
        #     }
        # )
        # self.conversation.append(
        #     {
        #         "role": "user",
        #         "content": "You can only ask me some questions from now on. Don't say anything other than a question. Please just say 'Explain the applicant.' if you understood my instructions.",
        #     }
        # )
        # self.conversation.append(
        #     {"role": "assistant", "content": "Explain the applicant."}
        # )
        # self.conversation.append(
        #     {
        #         "role": "user",
        #         "content": "Start the interview. I will apply to Naver as a front-end developer. Also, I am a new front-end applicant. Please prepare challenging and common questions for interviewers when applying for Naver Front Developer. If I answer, tell me okay and present me the next question you prepared earlier. Now ask the question.",
        #     },
        # )

        # Response객체를 생성하여 데이터와 상태 코드 반환
        return Response(transcription, status=status.HTTP_200_OK)

    def continue_conversation(self):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=self.conversation, temperature=0.9, n=1
        )

        message = completion.choices[0].message["content"]
        return message


# 상황 부여 면접
class SituationInterview(APIView):
    conversation = []
    # 처음 데이터를 받아야 하는 경우 -> 음성 데이터는 없음. 그냥 GPT 질문 시작.
    @swagger_auto_schema(
        operation_description="상황 면접 데이터 최초 받기",
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
    def default_tuning(self, seletor_name, job_name, career):
        # 대화 시작 메시지 추가
        self.conversation.append(
            {
                "role": "user",
                "contenet": 'function_name: [situation_interview] input: ["sector", "job", "career", "number_of_questions"] rule: [You are an expert in recruitment and interviewer specializing in finding the best talent. Ask questions that can judge my ability to cope with situations based “job” that I’ll provide.   You should create total of "number_of_questions" amount of questions, and provide it once at a time. For example, you would be ask such as "You have been assigned to work on a project where the design team has provided you with a visually appealing but intricate UI design for a web page. As you start implementing it, you realize that some of the design elements may not be feasible to achieve with the current technology or may negatively impact the performance. How would you handle this situation?" You should ask the next question only after I have answered to the question. Never ask a question similar to the previous one include example that i provide. Do not include any explanations or additional information in your response, simply provide a question in korean. ]'
                + "interviewee_info(Company="
                + seletor_name
                + ", Job="
                + job_name
                + ", Career="
                + career
                + ")",
            }
        )

        # self.conversation.append(
        #     {
        #         "role": "user",
        #         "content":"I think we'll work together to find possible alternatives or compromises. I think I will communicate with the design team and quickly share concerns to clarify the challenges and potential risks associated with the problematic design elements and coordinate the UI design."
        #     },
        # )
        # self.conversation.append(
        #     {
        #         "role": "user",
        #         "content": "Discuss issues with backend developers who have changed and provide a clear explanation of their impact on front-end functionality. And I think we'll work with back-end developers to find a solution that can solve the problem while maintaining the intended improvements. We will then have daily stand-up, regular meetings to facilitate communication between the front-end and back-end teams to avoid problems. Give me the next question in Korean only."
        #     },
        # )


# 심층 면접 인터뷰
class DeepInterview(APIView):
    conversation = []

    # 처음 데이터를 받아야 하는 경우 -> 음성 데이터는 없음. 그냥 GPT 질문 시작.
    @swagger_auto_schema(responses={"200": ResponseVoiceSerializer})

    def get(self, request):
        # 기본 튜닝
        self.default_tuning()

        # 대화 계속하기
        message = self.continue_conversation()

        # form_id 받기, 파라미터로 받기
        form_id = request.get.GET("form_id")

        # Question 테이블에 데이터 추가
        Question.objects.create(content=message, form_id=form_id)


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

        form_id = request.body["form_id"]
        question_id = request.body["question_id"]
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        transcription = transcript["text"]

        # S3에 업로드하는 로직 필요!

        # 답변 테이블에 추가

        Answer.objects.create(content=transcription, question_id=question_id)
        form_info = get_object_or_404(Form, id=form_id)
        questions = form_info.questions.all()

        # 기본 튜닝
        self.default_tuning()

        # 질문, 대답 추가.
        for question in questions:
            answer = question.answer
            self.add_question_answer(question, answer)

        message = self.continue_conversation()

        # 질문 테이블에 정보 추가
        Question.objects.create(content=message, form_id=form_id)

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
                "content": "I will apply to Naver as a front-end developer. Also, I am a new front-end applicant.",
            },
        )
        self.conversation.append(
            {"role": "assistant", "content": "sure. i understand."}
        )

        self.conversation.append(
            {
                "role": "user",
                "content": "Start the interview. I will apply to Naver as a front-end developer. Also, I am a new front-end applicant.",
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
            {"role": "assistant", "content": "sure. i understand."}
        )

        self.conversation.append(
            {
                "role": "user",
                "content": "Please describe any of your experiences so far that you are confident of achieving innovation. 'First challenge in front-end web development' I became interested in technology stacks in front-end web development that I had never encountered when I was undergraduate, and I studied by making projects personally during the second semester from the summer vacation of the fourth grade. I learned HTML and CSS natively and then created a project that uses the JavaScript framework. We selected React and Vue as representative JavaScript frameworks and created 'shopping mall site' and 'movie information search site', respectively. Although there are no objective figures or indicators to prove performance, I was confident that I had increased my web development capabilities in that I had created websites that functioned with technology actually used in my work. In the process of implementing a 'shopping mall site' using React, the components that make up the screen were not difficult to design and style, but there were difficulties in implementing the function of adding and removing products to the shopping cart. The process of using multiple hooks and contexts provided by React, such as useState, useCallback, and useMemo, was unfamiliar and took a long time to implement the function. The 'Movie Information Search Site' linked the movie search API and was the first website to be developed using the API. I used the OMDB API key for API linkage, but there is still a problem that the OMDB API key is exposed on the code, but I thought I became more familiar with Vue by making it using Vue router, bootstrap, and Vue for status management.",
            },
        )
        self.conversation.append(
            {"role": "assistant", "content": "sure. i understand."}
        )
        self.conversation.append(
            {
                "role": "user",
                "content": "Please indicate your discriminatory strengths in the job you want to apply for.'Communication skills and collaboration skills' Developers believe that collaboration is essential. In fact, if you work at the front end, you will basically communicate with planners, designers, and backend developers, but if you don't have full knowledge of development, I think there will be problems communicating in developmental languages. I studied computer science and theoretical knowledge thoroughly when I was an undergraduate, and most of my major subjects got 'A+' or 'A'. Working on team projects with this complete theoretical knowledge, I was able to choose terms that were as easy as possible to communicate and communicate with the other person easily. Thanks to this, there was no misunderstanding between members due to communication problems in the process of carrying out most team projects. If you do actual work, you may have technical communication or you may not understand it well in the process, but I will make sure that there is no problem with communication by asking politely again with activeness. In addition, I think 'activity' and 'grit' are also important for collaboration ability. When I was working on various team projects during my undergraduate years, including graduation projects, I always tried to find a solution when I encountered something I didn't know while playing my role. When I couldn't solve it, I used to ask politely with 'activity.' I think my 'activity' and 'grit' will motivate the members to collaborate.",
            },
        )
        self.conversation.append(
            {"role": "assistant", "content": "sure. i understand."}
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
                "content": "If you join the company, please describe the vision you dream of. The front-end development job is to develop everything the customer sees. In other words, I think it is making the first impression of Carrot Insurance because it is in charge of the first part that the customer sees. I find this work very attractive and I want to be a key member who can contribute to the development team that sees and reflects customer responses immediately. Devices and browsers are becoming more and more diverse, and in order to provide customers with a web environment that fits them, as a front-end developer, I will act as a reliable bridge between customers and Carrot Insurance. The front-end development sector is trending faster than other sectors. To keep up with this, I will try to learn new technologies and trends steadily without continuing to settle for one skill. We will always strive to implement the user interface and user experience technically and accurately through continuous learning, and we will think from your perspective. I think the expansion of online business will be more severe in the future. As a result, customers will be increasingly exposed to online websites, and I believe that the front-end development job has a vision. For me, who loves to learn and learn new skills, I am confident that Carrot Insurance's front-end development job is the best place to grow together with the competence. start interview",
            }
        )

        self.conversation.append(
            {
                "role": "user",
                "content": "Now you extract the above self-introduction specifically. Ask a famous and tricky question based on the this extraction. You don't have to show me the extract, just ask me question. and re-extract and ask question when you're done with the tail-biting method. and say only korean. and Don't say anything other than a question from now on. give me a question.",
            }
        )


# 성향 면접 인터뷰
class TendancyInterview(APIView):
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
                "content": "Start the interview. I will apply to Naver as a front-end developer. Also, I am a new front-end applicant. Please prepare challenging and common questions for interviewers when applying for Naver Front Developer. If I answer, tell me okay and present me the next question you prepared earlier. Now ask the question.",
            },
        )
        # 대화 계속하기
        message = self.continue_conversation()

        return Response(message, status=status.HTTP_200_OK)

    def continue_conversation(self):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=self.conversation, temperature=0.9, n=1
        )

        message = completion.choices[0].message["content"]
        return message
