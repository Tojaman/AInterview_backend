from django.forms import Form
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, redirect, render
from drf_yasg.utils import swagger_auto_schema
from forms.serializers import FormSerializer

# Create your views here.

# 지원정보 API
class FormsView(APIView):
    @swagger_auto_schema(tags=["form_list"], operation_id="get application informations")
    #지원정보 전체조회
    def get(self, request):
        data = Form.objects.all()
        serializer = FormSerializer(data, many=True)
        return Response(serializer.data, status=200)

    @swagger_auto_schema(request_body=FormSerializer, operation_id="get application informations")
    def post(self, request):
        serializer = FormSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=404)
    

class FormView(APIView):   
    #사용자별 지원정보 전체조회
    def get(self, request, pk):
        data = Form.objects.filter(id=pk)
        serializer = FormSerializer(data, many=True)
        return Response(serializer.data, status=200) 
    
    #사용자별 지원 데이터 상세조회
    def get(self, request, pk):
        data = get_object_or_404(Form, pk=pk)
        serializer = FormSerializer(data)      
        return Response(serializer.data)
    
    #지원정보 추가

    
    #지원정보 삭제
    def delete(self, request, pk):
        info = get_object_or_404(Form, id=pk)
        info.delete()
        return redirect('form_list')
    
    #지원정보 수정
    def put(self, request, pk):
        info = get_object_or_404(Form, id=pk)
        serializer = FormSerializer(info, data=request.data) 
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=404)