from django.db import models
from django.conf import settings
from django.utils import timezone

class Message(models.Model):
    subject = models.CharField(max_length=255, null=True, blank=True)
    body = models.TextField()
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='received_messages')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_trashed = models.BooleanField(default=False)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.subject} - {self.sender}"

    def mark_as_read(self, user):
        # Update or create the read status
        read_status, created = MessageReadStatus.objects.get_or_create(user=user, message=self)
        if not read_status.read_at:
            read_status.read_at = timezone.now()
            read_status.save()

        # Update the unread status without deleting or setting created_at to None
        unread_status, _ = MessageUnreadStatus.objects.get_or_create(user=user, message=self)
        if unread_status.created_at is not None:
            unread_status.created_at = timezone.now()  # Keep the timestamp but update it
            unread_status.save()


class MessageReadStatus(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.message.subject} - {'Read' if self.read_at else 'Unread'}"


class MessageUnreadStatus(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Unread by {self.user} - {self.message.subject}"