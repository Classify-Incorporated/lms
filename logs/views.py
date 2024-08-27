from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from .models import SubjectLog
from django.contrib.auth.decorators import login_required
# Create your views here.

@login_required
def subjectLogDetails(request):
    latest_logs = SubjectLog.objects.all().order_by('-created_at')[:5]  # Get the 5 most recent logs
    return render(request, 'logs/subjectLogDetails.html', {
        'latest_logs': latest_logs,
    })
