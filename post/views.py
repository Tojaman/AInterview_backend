from django.http import JsonResponse
from rest_framework.views import APIView

from .models import Post
from .serializers import PostSerializer
from drf_yasg.utils import swagger_auto_schema


# 면접을 위한 정보 입력, Post와 Get 구현
class PostApplication(APIView):
    @swagger_auto_schema(operation_id="input application information for interview question")
    def post(self, request):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=200)
        return JsonResponse(serializer.errors, status=404)
    @swagger_auto_schema(operation_id="get application information")
    def get(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id)
            serializer = PostSerializer(post)
            return JsonResponse(serializer.data)
        
        except Post.DoesNotExist:
            return JsonResponse(serializer.errors, status=404)
