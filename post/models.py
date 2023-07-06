from django.utils import timezone
from django.db import models

default=timezone.now

class Post(models.Model):
    sector_name = models.CharField(max_length=100)
    job_name = models.CharField(max_length=100)
    career = models.CharField(max_length=20, default='신입')
    resume = models.CharField(max_length=10000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.job_name} in {self.sector_name}"