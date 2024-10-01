
from django.shortcuts import render, get_object_or_404, redirect
from .models import SubjectLog, UserSubjectLog
from django.contrib.auth.decorators import login_required
# Create your views here.

@login_required
def subjectLogDetails(request):
    latest_logs = SubjectLog.objects.all().order_by('-created_at')[:5]  # Get the 5 most recent logs
    return render(request, 'logs/subjectLogDetails.html', {
        'latest_logs': latest_logs,
    })

def mark_log_as_read(request, log_id):
    if request.user.is_authenticated:
        log = get_object_or_404(SubjectLog, id=log_id)
        user_log, created = UserSubjectLog.objects.get_or_create(user=request.user, subject_log=log)
        user_log.read = True
        user_log.save()
        return redirect('subjectDetail', pk=log.subject.id)
    