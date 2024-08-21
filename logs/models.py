from django.db import models
from subject.models import Subject

class SubjectLog(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for {self.subject.subject_name} at {self.created_at}"