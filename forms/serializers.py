from rest_framework import serializers
from .models import Form

class FormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = ('user_id','sector_name', 'job_name', 'career', 'resume')