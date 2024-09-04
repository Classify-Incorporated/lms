from django.shortcuts import render, redirect, get_object_or_404
from .forms import subjectForm
from .models import Subject
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from course.models import Semester
from django.http import JsonResponse
from .models import Subject
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import permission_required
# Create your views here.

#Subject List
@login_required
@permission_required('subject.view_subject', raise_exception=True)
def subjectList(request):
    today = timezone.now().date()
    current_semester = Semester.objects.filter(start_date__lte=today, end_date__gte=today).first()

    if request.user.profile.role.name.lower() == 'teacher':
        subjects = Subject.objects.filter(assign_teacher=request.user, subjectenrollment__semester=current_semester).distinct()
    else:
        subjects = Subject.objects.filter(subjectenrollment__semester=current_semester).distinct()

    form = subjectForm()

    return render(request, 'subject/subject.html', {'subjects': subjects, 'form': form})

#Create Subject
@login_required
@permission_required('subject.add_subject', raise_exception=True)
def createSubject(request):
    if request.method == 'POST':
        form = subjectForm(request.POST, request.FILES)
        if form.is_valid():
            # Check for duplicate subject name
            subject_name = form.cleaned_data.get('subject_name')
            if Subject.objects.filter(subject_name=subject_name).exists():
                messages.error(request, 'Subject name already exists. Please choose another name.')
                return redirect('createSubject')

            form.save()
            messages.success(request, 'Subject created successfully!')
            return redirect('subject')
        else:
            messages.error(request, 'There was an error creating the subject. Please try again.')
    else:
        form = subjectForm()

    return render(request, 'subject/createSubject.html', {'form': form})

#Modify Subject
@login_required
@permission_required('subject.change_subject', raise_exception=True)
def updateSubject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        form = subjectForm(request.POST, request.FILES, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject updated successfully!')
            return redirect('subject')
        else:
            messages.error(request, 'There was an error updated the subject. Please try again.')
    else:
        form = subjectForm(instance=subject)
    
    return render(request, 'subject/updateSubject.html', {'form': form, 'subject': subject})


#Delete Subject
@login_required
@permission_required('subject.delete_subject', raise_exception=True)
def deleteSubject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    subject.delete()
    messages.success(request, 'Subject deleted successfully!')
    return redirect('subject')

@csrf_exempt
def check_duplicate_subject(request):
    if request.method == 'POST':
        subject_name = request.POST.get('subject_name')
        is_duplicate = Subject.objects.filter(subject_name=subject_name).exists()
        return JsonResponse({'is_duplicate': is_duplicate})