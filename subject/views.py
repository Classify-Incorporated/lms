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
from datetime import date
from course.models import Semester, SubjectEnrollment
from datetime import datetime
# Create your views here.

#Subject List
@login_required
@permission_required('subject.view_subject', raise_exception=True)
def subjectList(request):
    today = date.today()
    current_semester = Semester.objects.filter(start_date__lte=today, end_date__gte=today).first()

    user_role = request.user.profile.role.name.lower()

    # If user is registrar, display all subjects regardless of the semester
    if user_role == 'registrar':
        subjects = Subject.objects.all()
    else:
        if current_semester:
            if user_role == 'teacher':
                # For teachers, filter by assigned subjects and current semester
                subjects = Subject.objects.filter(
                    assign_teacher=request.user,
                    id__in=SubjectEnrollment.objects.filter(semester=current_semester).values_list('subject_id', flat=True)
                )
            else:
                # For students or other users, filter subjects by current semester
                subjects = Subject.objects.filter(
                    id__in=SubjectEnrollment.objects.filter(semester=current_semester).values_list('subject_id', flat=True)
                )
        else:
            if user_role == 'teacher':
                # If no current semester, filter subjects by teacher
                subjects = Subject.objects.filter(assign_teacher=request.user)
            else:
                # Show all subjects for other users if no current semester
                subjects = Subject.objects.all()

    form = subjectForm()
    return render(request, 'subject/subject.html', {'subjects': subjects, 'form': form})

#Create Subject
@login_required
@permission_required('subject.add_subject', raise_exception=True)
def createSubject(request):
    errors = []

    if request.method == 'POST':
        form = subjectForm(request.POST, request.FILES)

        subject_name = request.POST.get('subject_name')
        subject_short_name = request.POST.get('subject_short_name')
        subject_code = request.POST.get('subject_code')
        schedule_start_time = request.POST.get('schedule_start_time')
        schedule_end_time = request.POST.get('schedule_end_time')
        assign_teacher = request.POST.get('assign_teacher')

        if not subject_name or not schedule_start_time or not schedule_end_time or not assign_teacher:
            messages.error(request,"All required fields must be filled in.")
            return redirect('subject')

        else:
            try:
                # Convert start and end time strings to time objects for comparison
                schedule_start_time = datetime.strptime(schedule_start_time, '%H:%M').time()
                schedule_end_time = datetime.strptime(schedule_end_time, '%H:%M').time()
            except ValueError:
                messages.error(request,"Invalid time format. Please enter time in 'HH:MM' format.")
                return redirect('subject')

            if schedule_start_time and schedule_end_time:
                if schedule_start_time >= schedule_end_time:
                    messages.error(request,"End time must be after the start time.")
                    return redirect('subject')

                # Check for duplicate subject based on subject details and schedule
                overlapping_subjects = Subject.objects.filter(
                    subject_name=subject_name,
                    subject_short_name=subject_short_name,
                    subject_code=subject_code,
                    assign_teacher=assign_teacher
                    ).filter(
                    # Check if the new semester's start date falls within an existing semester
                    schedule_start_time__lt=schedule_end_time,  # The existing semester starts before or on the new semester's end date
                    schedule_end_time__gt=schedule_start_time   # The existing semester ends after or on the new semester's start date
                    )

                if overlapping_subjects.exists():
                    messages.error(request,"A subject with the same name and schedule already exists for this teacher. Please assign a different teacher.")
                    return redirect('subject')
                
        if not errors and form.is_valid():
            # Save the form if no duplicate subject exists
            form.save()
            messages.success(request, 'Subject created successfully!')
            return redirect('subject')

        else:
            messages.error(request, 'There was an error creating the subject. Please try again.')
        return redirect('subject')

    else:
        form = subjectForm()

    return render(request, 'subject/createSubject.html', {'form': form})

#Modify Subject
@login_required
@permission_required('subject.change_subject', raise_exception=True)
def updateSubject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    errors = []

    if request.method == 'POST':
        form = subjectForm(request.POST, request.FILES, instance=subject)

        subject_name = request.POST.get('subject_name')
        subject_short_name = request.POST.get('subject_short_name')
        subject_code = request.POST.get('subject_code')
        schedule_start_time = request.POST.get('schedule_start_time')
        schedule_end_time = request.POST.get('schedule_end_time')
        assign_teacher = request.POST.get('assign_teacher')

        print("Schedule Start Time:", schedule_start_time)
        print("Schedule End Time:", schedule_end_time)


        if not subject_name or not schedule_start_time or not schedule_end_time or not assign_teacher:
            messages.error(request, "All required fields must be filled in.")
            return redirect('subject')

        else:
            try:
                # Try to parse the time in HH:MM:SS format first
                schedule_start_time = datetime.strptime(schedule_start_time, '%H:%M:%S').time()
                schedule_end_time = datetime.strptime(schedule_end_time, '%H:%M:%S').time()
            except ValueError:
                try:
                    # Fall back to parsing in HH:MM format if the above fails
                    schedule_start_time = datetime.strptime(schedule_start_time, '%H:%M').time()
                    schedule_end_time = datetime.strptime(schedule_end_time, '%H:%M').time()
                except ValueError:
                    messages.error(request, "Invalid time format. Please enter time in 'HH:MM' or 'HH:MM:SS' format.")
                    return redirect('subject')

            if schedule_start_time and schedule_end_time:
                # Check if the start time is after or equal to the end time
                if schedule_start_time >= schedule_end_time:
                    messages.error(request, "End time must be after the start time.")
                    return redirect('subject')

                # Check for overlapping subjects based on subject details and schedule
                overlapping_subjects = Subject.objects.filter(
                    subject_name=subject_name,
                    subject_short_name=subject_short_name,
                    subject_code=subject_code,
                    assign_teacher=assign_teacher
                ).exclude(pk=subject.pk)  # Exclude the current subject being updated
                overlapping_subjects = overlapping_subjects.filter(
                    schedule_start_time__lt=schedule_end_time,  # The existing subject starts before the new subject's end time
                    schedule_end_time__gt=schedule_start_time   # The existing subject ends after the new subject's start time
                )

                if overlapping_subjects.exists():
                    messages.error(request, "A subject with the same name and schedule already exists for this teacher. Please assign a different teacher.")
                    return redirect('subject')

        if not errors and form.is_valid():
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