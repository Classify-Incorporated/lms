from django.db import models
from subject.models import Subject
import os
import uuid


def get_upload_file(instance, filename):
    filename = f"{uuid.uuid4()}{os.path.splitext(filename)[1]}"
    return os.path.join('module', filename)


def get_scorm_upload_path(instance, filename):
    filename = f"{uuid.uuid4()}{os.path.splitext(filename)[1]}"
    return os.path.join('scormPackages', filename)


# Create your models here.
class Module(models.Model):
    file_name = models.CharField(max_length=100)
    file = models.FileField(upload_to=get_upload_file, null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    def __str__(self):
        return self.file_name
    
class SCORMPackage(models.Model):
    package_name = models.CharField(max_length=100)
    pptx_link = models.URLField(max_length=200, null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    def __str__(self):
        return self.package_name

    # You can keep the save method as is if you plan to add SCORM conversion later
    # Or remove the conversion logic if it's not needed for now
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Placeholder for future SCORM conversion logic