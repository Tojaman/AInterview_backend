from django.db import models

class Post(models.Model):
    sector_name = models.CharField(max_length=100)
    job_name = models.CharField(max_length=100)
    career = models.CharField(max_length=20, default='신입')
    resume = models.CharField(max_length=20000)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.job_name} in {self.sector_name}"