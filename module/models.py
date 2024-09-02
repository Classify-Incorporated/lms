from django.db import models
from subject.models import Subject
import os
import uuid
from pptx import Presentation
import fitz  
from logs.models import SubjectLog
from django.conf import settings
import requests
from PIL import Image, ImageDraw
import subprocess


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

    def convert_pptx_to_images(self):
        image_paths = []
        output_dir = os.path.join(settings.MEDIA_ROOT, 'scorm_images', self.package_name)
        os.makedirs(output_dir, exist_ok=True)

        # Load the presentation
        presentation = Presentation(self.file.path)

        # Convert each slide to an image
        for i, slide in enumerate(presentation.slides):
            image_path = os.path.join(output_dir, f'slide_{i + 1}.jpg')
            slide.get_thumbnail().save(image_path, 'JPEG')
            image_paths.append(image_path)

        return image_paths