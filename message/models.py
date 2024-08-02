# models.py
from django.db import models
from django.conf import settings


class Message(models.Model):
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='received_messages')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject

class MessageReadStatus(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.message.subject} - {'Read' if self.read_at else 'Unread'}"
