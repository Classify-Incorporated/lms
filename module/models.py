from django.db import models
from subject.models import Subject
import os
import uuid
from logs.models import SubjectLog
from zipfile import ZipFile

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
    course_id = models.CharField(max_length=255, unique=True, null=True)  # Add this field

    def __str__(self):
        return self.package_name

    def validate_scorm_package(self):
        # Ensure the file is a zip file
        if not self.file.name.endswith('.zip'):
            print("File is not a zip file.")
            return False

        try:
            # Open the zip file and check for imsmanifest.xml in the root
            with ZipFile(self.file.path, 'r') as zip_file:
                namelist = zip_file.namelist()
                print("Files in zip:", namelist)  # Debugging: List all files in the zip

                if 'imsmanifest.xml' in namelist:
                    print("Found imsmanifest.xml")
                    return True
                else:
                    print("imsmanifest.xml not found in the root directory of the zip file.")
        except Exception as e:
            print(f"Exception occurred during SCORM validation: {e}")
            return False

        return False

    def save(self, *args, **kwargs):
        if not self.course_id:  # Generate a unique course_id if not set
            self.course_id = f"{self.subject.id}-{uuid.uuid4()}"
        
        is_new = self.pk is None
        super().save(*args, **kwargs)  # Save the file first to ensure it is available for validation

        if is_new:
            self.is_scorm = self.validate_scorm_package()
            super().save(update_fields=['is_scorm'])  # Update after validation

            SubjectLog.objects.create(
                subject=self.subject,
                message=f"A new SCORM package named '{self.package_name}' has been created for {self.subject.subject_name}. Valid SCORM: {self.is_scorm}"
            )