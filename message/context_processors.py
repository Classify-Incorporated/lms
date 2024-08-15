from django.utils import timezone
from .models import MessageReadStatus

def unread_messages_count(request):
    if request.user.is_authenticated:
        unread_count = MessageReadStatus.objects.filter(user=request.user, read_at__isnull=True).count()
    else:
        unread_count = 0
    return {'unread_messages_count': unread_count}
