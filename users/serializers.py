from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate

# 유저 불러오기
User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get("email", "")
        password = data.get("password", "")

        if email and password:
            print(self.context.get("request"))

            user = authenticate(
                request=self.context.get("request"), email=email, password=password
            )

            if user is None:
                raise serializers.ValidationError("이메일 혹은 비밀번호가 틀렸습니다.")
            # soft-delete된 사용자일 시 발생시키는 부분. 아직 해당 기능구현 없음.
            if not user.is_active:
                raise serializers.ValidationError("삭제된 계정입니다. ")
        else:
            raise serializers.ValidationError("이메일과 비밀번호를 입력하세요.")

        data["user"] = user
        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "password2")

    def validate_email(self, value):
        # Check if the email is already in use
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 존재하는 계정입니다.")
        return value

    def save(self, **kwargs):
        user = User(
            username=self.validated_data["username"],
            email=self.validated_data["email"],
        )
        password = self.validated_data["password"]
        password2 = self.validated_data["password2"]

        if password != password2:
            raise serializers.ValidationError({"password": "비밀번호가 일치하지 않습니다."})
        user.set_password(password)
        user.save()
        return user


# LogoutView에서 post method swagger test시 request_body로 활용
class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField(help_text="Refresh token")


# uncomment below code block in case we have to return user information in LoginView
# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['id', 'username', 'email', 'password', 'date_joined']
#         extra_kwargs = {'password': {'write_only': True}}
#
#     def create(self, validated_data):
#         password = validated_data.pop('password')
#         user = User(**validated_data)
#         user.set_password(password)
#         user.save()
#         return user
