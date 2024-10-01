from django.db import models
from subject.models import Subject
from accounts.models import CustomUser

class SubjectLog(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    activity = models.BooleanField(default=False)

    def __str__(self):
        return f"Log for {self.subject.subject_name} at {self.created_at}"

class UserSubjectLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    subject_log = models.ForeignKey(SubjectLog, on_delete=models.CASCADE)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.subject_log.message} - Read: {self.read}"