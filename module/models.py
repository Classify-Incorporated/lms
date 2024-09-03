from django.db import models
from subject.models import Subject
import os
import uuid
from logs.models import SubjectLog
from django.dispatch import receiver
from django.core.files.base import ContentFile
from django.utils import timezone

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

class SCORMPackage(models.Model):
    package_name = models.CharField(max_length=100)
    file = models.FileField(upload_to=get_scorm_upload_path, null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    is_scorm = models.BooleanField(default=False)
    course_id = models.CharField(max_length=255, unique=True, null=True)
    image_paths = models.JSONField(default=list, blank=True)  # Store paths to generated images
    video_paths = models.JSONField(default=list, blank=True)  # Store paths to videos
    pdf_pages = models.JSONField(default=list, blank=True)  # Store paths to PDF pages converted to images

    def __str__(self):
        return self.package_name
    
class StudentProgress(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    scorm_package = models.ForeignKey(SCORMPackage, on_delete=models.CASCADE, null=True, blank=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, blank=True)
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # progress as a percentage
    completed = models.BooleanField(default=False)
    first_accessed = models.DateTimeField(null=True, blank=True)  # First access date
    last_accessed = models.DateTimeField(auto_now=True)  # Last access date
    time_spent = models.IntegerField(default=0) 
    last_page = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.student.username} - {self.scorm_package or self.module} - {self.progress}%"
    
    def save(self, *args, **kwargs):
        now = timezone.now()
        
        # If first_accessed is not set, set it now
        if not self.first_accessed:
            self.first_accessed = now
        
        # If there is a previous last_accessed time, calculate the time spent since the last access
        if self.last_accessed:
            time_delta = now - self.last_accessed
            self.time_spent += int(time_delta.total_seconds())

        # Update the last_accessed time
        self.last_accessed = now

        super(StudentProgress, self).save(*args, **kwargs)