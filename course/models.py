from django.db import models
from accounts.models import CustomUser
from subject.models import Subject
# Create your models here.

class Course(models.Model):
    course_name = models.CharField(max_length=100)
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    def __str__(self):
        return self.course_name