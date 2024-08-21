from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from .models import SubjectLog
from subject.models import Subject
# Create your views here.

def subjectLogDetails(request,):
    latest_log = SubjectLog.objects.all().order_by('-created_at').first()  # Fetch the latest log
    print(latest_log)
    return render(request, 'logs/subjectLogDetails.html', {
        'latest_log': latest_log,
    })