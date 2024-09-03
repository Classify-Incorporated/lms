from django.db import models
from subject.models import Subject
import os
import uuid
from logs.models import SubjectLog
from django.dispatch import receiver
from django.core.files.base import ContentFile

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
    
    def convert_ppt_to_pdf(self):
        if self.file and self.file.name.endswith('.pptx'):
            try:
                pptx_path = self.file.path
                pdf_path = os.path.splitext(pptx_path)[0] + '.pdf'

                # Load the presentation
                presentation = Presentation(pptx_path)
                
                # Convert the presentation to PDF format
                presentation.save(pdf_path, SaveFormat.PDF)

                # Save the converted PDF back to the model
                with open(pdf_path, 'rb') as pdf_file:
                    self.file.save(os.path.basename(pdf_path), ContentFile(pdf_file.read()))
                
                os.remove(pdf_path)  # Optionally remove the PDF after saving
            except Exception as e:
                # Handle errors, such as logging them
                print(f"Error converting PPTX to PDF: {e}")
                # Optionally, add custom error handling logic here

# Signal to handle file conversion after save
@receiver(models.signals.post_save, sender=SCORMPackage)
def post_save_scorm_package(sender, instance, **kwargs):
    if instance.file and instance.file.name.endswith('.pptx'):
        instance.convert_ppt_to_pdf()
