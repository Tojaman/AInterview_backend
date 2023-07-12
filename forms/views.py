from django.forms import Form
from drf_yasg import openapi
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, redirect, render
from drf_yasg.utils import swagger_auto_schema
from forms.serializers import FormsSerializer, FormCreateSerializer


# Create your views here.

# 지원정보 API
class FormsAllView(APIView):

    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["forms_all"], operation_id="get application informations")
    #지원정보 전체조회
    def get(self, request):
        data = Form.objects.all()
        serializer = FormsSerializer(data, many=True)
        return Response(serializer.data, status=200)

    # 지원정보 추가
    parameter_token = openapi.Parameter(
        "Authorization",
        openapi.IN_HEADER,
        description="access_token",
        type=openapi.TYPE_STRING
    )
    @swagger_auto_schema(request_body=FormsSerializer,  manual_parameters = [parameter_token], operation_id="post application informations")
    def post(self, request):
        serializer = FormCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user_id=request.user.id) #사용자의 id를 user_id 필드에 저장
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=404)
    

class FormsUserView(APIView):
    #사용자별 지원정보 전체조회
    def get(self, request):
        data = Form.objects.filter(user_id = request.user.id)
        serializer = FormsSerializer(data, many=True)
        return Response(serializer.data, status=200) 
    
    #사용자별 지원정보 상세조회
    def get(self, request, pk):
        data = get_object_or_404(Form, pk=pk)
        serializer = FormsSerializer(data)
        return Response(serializer.data)

    #지원정보 삭제
    def delete(self, request, pk):
        info = get_object_or_404(Form, pk=pk)
        info.delete()
        return redirect('form_list')
    
    #지원정보 수정
    def put(self, request, pk):
        info = get_object_or_404(Form, pk=pk)
        serializer = FormsSerializer(info, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=404)