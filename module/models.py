from django.db import models
from subject.models import Subject

# Create your models here.
class Module(models.Model):
    file_name = models.CharField(max_length=100)
    file = models.FileField(upload_to='modules/')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    def __str__(self):
        return self.file_name
    