from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, LoginSerializer, RefreshTokenSerializer
from django.contrib.auth import get_user_model

# 유저 모델 불러오기
User = get_user_model()

# 회원가입
class RegisterView(APIView):
    parser_classes = [JSONParser]
    serializer_class = RegisterSerializer

    @swagger_auto_schema(
        request_body=RegisterSerializer,
        operation_id="회원 가입",
        responses={200: RegisterSerializer(many=False)}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 로그인
class LoginView(generics.GenericAPIView):
    parser_classes = [JSONParser]
    serializer_class = LoginSerializer

    @swagger_auto_schema(operation_id="사용자 로그인")
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        # refresh token, access token
        return Response({
            # uncomment below code to also return user information, else just remove
            # "user": UserSerializer(user, context=self.get_serializer_context()).data
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })


# 로그아웃
class LogoutView(APIView):
    parser_classes = [JSONParser]
    @swagger_auto_schema(
        request_body=RefreshTokenSerializer,
        operation_id="로그아웃 (토큰 blacklist)"
    )
    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            # 로그아웃 시 해당 token을 blacklist해서 auth를 위해 사용 불가하게 만든다.
            token.blacklist()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


# soft-delete
class DeleteUserView(generics.DestroyAPIView):
    queryset = User.objects.all()
    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)