
from django.shortcuts import render, get_object_or_404, redirect
from .models import SubjectLog
from django.contrib.auth.decorators import login_required
# Create your views here.

@login_required
def subjectLogDetails(request):
    latest_logs = SubjectLog.objects.all().order_by('-created_at')[:5]  # Get the 5 most recent logs
    return render(request, 'logs/subjectLogDetails.html', {
        'latest_logs': latest_logs,
    })

def mark_log_as_read(request, log_id):
    # Get the log by its ID and mark it as read
    log = get_object_or_404(SubjectLog, id=log_id)
    log.read = True
    log.save()

    return redirect('subjectDetail', pk=log.subject.id)