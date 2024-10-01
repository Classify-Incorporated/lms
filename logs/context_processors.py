# context_processors.py
from .models import SubjectLog

def subject_logs(request):
    if request.user.is_authenticated:

        logs = SubjectLog.objects.filter(message__icontains='activity' ).order_by('-created_at')[:5] 
        unread_count = SubjectLog.objects.filter(message__icontains='activity', read=False).order_by('-created_at')[:5].count()  # Limit to first 5 logs
        read_count = SubjectLog.objects.filter(message__icontains='activity', read=True).order_by('-created_at')[:5].count()

        if unread_count < read_count:
            count = 0
        else:
            count = unread_count - read_count

        return {
            'logs': logs,
            'unread_notifications_count': count
        }
    return {}
