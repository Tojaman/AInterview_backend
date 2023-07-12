from django.db import models
from users.models import User


class Form(models.Model):
    user_id = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="forms", db_column="user_id"
    )
    sector_name = models.CharField(max_length=100, null=False)
    job_name = models.CharField(max_length=100, null=False)
    career = models.CharField(max_length=20, default="신입", null=False)
    resume = models.CharField(max_length=10000, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)

    def __str__(self):
        return f"{self.job_name} in {self.sector_name}"
