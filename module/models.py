from django.db import models
from subject.models import Subject
import os
import uuid
from logs.models import SubjectLog
from django.utils import timezone
from course.models import Term

from django.conf import settings
def get_upload_file(instance, filename):
    filename = f"{uuid.uuid4()}{os.path.splitext(filename)[1]}"
    return os.path.join('module', filename)

def get_scorm_upload_path(instance, filename):
    filename = f"{uuid.uuid4()}{os.path.splitext(filename)[1]}"
    return os.path.join('scormPackages', filename)

class Module(models.Model):
    file_name = models.CharField(max_length=100)
    file = models.FileField(upload_to=get_upload_file, null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    url = models.URLField(max_length=200, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, blank=True) 
    display_lesson_for_selected_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='modules_visible') 
    allow_download = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)


    def __str__(self):
        return self.file_name
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Check if the object is new (not yet saved)
        super().save(*args, **kwargs)
        if is_new:
            SubjectLog.objects.create(
                subject=self.subject,
                message=f"A new module named '{self.file_name}' has been created for {self.subject.subject_name}."
            )
    
class StudentProgress(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, blank=True)
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0) 
    completed = models.BooleanField(default=False)
    first_accessed = models.DateTimeField(null=True, blank=True)  
    last_accessed = models.DateTimeField(auto_now=True)  
    time_spent = models.IntegerField(default=0)  
    last_page = models.IntegerField(default=1) 

    def __str__(self):
        return f"{self.student.username} - {self.module.file_name} - {self.progress}%"

    def save(self, *args, **kwargs):
        now = timezone.now()

        if not self.first_accessed:
            self.first_accessed = now

        if self.last_accessed:
            time_delta = now - self.last_accessed
            self.time_spent += int(time_delta.total_seconds()) 

        self.last_accessed = now 

        super(StudentProgress, self).save(*args, **kwargs)