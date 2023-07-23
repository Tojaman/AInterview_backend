from django.db import models
from django.utils import timezone
from forms.models import Form


# Question과 Answer는 1대 1관계, form과 question은 1대 N관계
class Question(models.Model):
    question_id = models.AutoField(primary_key=True, db_column="question_id")
    content = models.TextField()
    form_id = models.ForeignKey(
        Form, related_name="questions", on_delete=models.CASCADE, db_column="form_id"
    )
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
    question_id = models.OneToOneField(Question, on_delete=models.CASCADE, related_name="answer")
    recode_file = models.CharField(max_length=200)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(blank=True, null=True)

    # 나중에 수정 시에 사용
    def update_date(self):
        self.updated_at = timezone.now()
        self.save()

    class Meta:
        db_table = "answer"

class GPTAnswer(models.Model):
    gptanswer_id = models.AutoField(primary_key=True, db_column="question_id")
    content = models.TextField()
    question_id = models.OneToOneField(
        Question, on_delete=models.CASCADE, related_name="gptanswer"
    )
    recode_file = models.CharField(max_length=200)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(blank=True, null=True)

    # 나중에 수정 시에 사용
    def update_date(self):
        self.updated_at = timezone.now()
        self.save()

    class Meta:
        db_table = "gptanswer"

