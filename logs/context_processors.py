# context_processors.py
from .models import SubjectLog

def subject_logs(request):
    if request.user.is_authenticated:

        logs = SubjectLog.objects.filter(activity=True ).order_by('-created_at')[:5] 
        count = [log for log in logs if not log.read]

        return {
            'logs': logs,
            'unread_notifications_count': len(count)
        }
    return {}
