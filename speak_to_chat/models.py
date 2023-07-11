from django.db import models
from django.utils import timezone

class Question(models.Model):
    question_id = models.AutoField(primary_key=True, db_column="question_id")
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(blank=True, null=True)
    
    
    # 나중에 수정 시에 사용
    def update_date(self):
        self.updated_at = timezone.now()
        self.save()
    
    class Meta:
        db_table = "question"
    
    
class Answer(models.Model):
    answer_id = models.AutoField(primary_key=True, db_column="answer_id")
    content = models.TextField()
    recode_file = models.CharField(max_length=200)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(blank=True, null=True)
    
    # 나중에 수정 시에 사용
    def update_date(self):
        self.updated_at = timezone.now()
        self.save()
        

    class Meta:
        db_table = "answer"
    
    

