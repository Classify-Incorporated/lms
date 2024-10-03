from django.db import models
from accounts.models import CustomUser
import os
import uuid
# Create your models here.

def get_upload_path(instance, filename):
    filename = f"{uuid.uuid4()}{os.path.splitext(filename)[1]}"
    return os.path.join('subjectPhoto', filename)

class Subject(models.Model):
    subject_name = models.CharField(max_length=100)
    subject_short_name = models.CharField(max_length=10, null= True, blank=True)
    subject_photo = models.ImageField(upload_to=get_upload_path, null=True, blank=True)
    assign_teacher = models.ForeignKey(CustomUser, on_delete=models.PROTECT, null=True, blank=True)
    subject_description = models.TextField(null=True, blank=True)
    subject_code = models.CharField(max_length=10, null=True, blank=True)
    schedule_start_time = models.TimeField(null=True, blank=True)
    schedule_end_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return self.subject_name
    

