from django.shortcuts import render, redirect, get_object_or_404
from .models import SubjectEnrollment, Semester, Term, Retake, StudentParticipationScore
from accounts.models import Profile
from subject.models import Subject
from roles.models import Role
from module.models import Module
from activity.models import Activity ,StudentQuestion, ActivityQuestion
from django.views import View
import json
from django.core.serializers.json import DjangoJSONEncoder
from accounts.models import CustomUser
from django.utils import timezone
from .forms import semesterForm, termForm
from django.db.models import Q
from django.contrib.auth.decorators import login_required

# Handle the enrollment of irregular students

class enrollStudentView(View):
    def post(self, request, *args, **kwargs):
        student_profile_id = request.POST.get('student_profile')
        subject_ids = request.POST.getlist('subject_ids')
        semester_id = request.POST.get('semester_id')

        student_profile = get_object_or_404(Profile, id=student_profile_id)
        student = student_profile.user
        subjects = Subject.objects.filter(id__in=subject_ids)
        semester = get_object_or_404(Semester, id=semester_id)

        for subject in subjects:
            subject_enrollment, created = SubjectEnrollment.objects.get_or_create(
                student=student,
                subject=subject,
                semester=semester
            )

            if not created:
                Retake.objects.create(subject_enrollment=subject_enrollment, reason="Retake due to failure or other reason")

        return redirect('subjectDetail', pk=subject.pk)

# Add Irregular Student
@login_required
def enrollStudent(request):
    student_role = Role.objects.get(name__iexact='student')
    profiles = Profile.objects.filter(role=student_role)
    subjects = Subject.objects.all()
    semesters = Semester.objects.all()

    profiles_json = json.dumps(list(profiles.values('id', 'first_name', 'last_name', 'student_status')), cls=DjangoJSONEncoder)
    
    return render(request, 'course/subjectEnrollment/enrollStudent.html', {
        'profiles': profiles,
        'profiles_json': profiles_json,
        'subjects': subjects,
        'semesters': semesters
    })


# Display the module based on the subject
@login_required
def subjectDetail(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    user = request.user

    is_student = user.is_authenticated and user.profile.role.name.lower() == 'student'
    is_teacher = user.is_authenticated and user.profile.role.name.lower() == 'teacher'

    now = timezone.localtime(timezone.now())

    # Get the selected semester from the request parameters
    selected_semester_id = request.GET.get('semester')
    if selected_semester_id and selected_semester_id != 'None':
        selected_semester = get_object_or_404(Semester, id=selected_semester_id)
    else:
        # Default to the current semester
        selected_semester = Semester.objects.filter(start_date__lte=now, end_date__gte=now).first()

    # Check if the selected semester is the current semester
    current_semester = Semester.objects.filter(start_date__lte=now, end_date__gte=now).first()
    in_current_semester = (selected_semester == current_semester)

    # Retrieve all terms associated with the selected semester
    terms = Term.objects.filter(semester=selected_semester)

    if is_student:
        # Get activities where the student has completed them with score > 0 and status is True
        completed_activities = StudentQuestion.objects.filter(
            student=user,
            score__gt=0,
            status=True
        ).values_list('activity_question__activity_id', flat=True).distinct()

        # Get activities where the student has answered essays
        answered_essays = StudentQuestion.objects.filter(
            student=user,
            activity_question__quiz_type__name='Essay',
            student_answer__isnull=False
        ).values_list('activity_question__activity_id', flat=True).distinct()

        # Get activities where the student has uploaded documents
        answered_documents = StudentQuestion.objects.filter(
            student=user,
            activity_question__quiz_type__name='Document',
            uploaded_file__isnull=False,
            status=True
        ).values_list('activity_question__activity_id', flat=True).distinct()

        # Exclude activities where submission_time is not null (activity has been submitted)
        submitted_activities = StudentQuestion.objects.filter(
            student=user,
            submission_time__isnull=False
        ).values_list('activity_question__activity_id', flat=True).distinct()

        # Combine all excluded activities
        excluded_activities = completed_activities.union(answered_essays, answered_documents, submitted_activities)

        # Display all activities for the subject, regardless of term, excluding completed ones
        activities = Activity.objects.filter(subject=subject).exclude(id__in=excluded_activities)

        # Display all finished activities
        finished_activities = Activity.objects.filter(
            subject=subject,
            end_time__lte=timezone.now()
        )

        # Filter activities based on their timing
        upcoming_activities = activities.filter(start_time__gt=timezone.now())
        ongoing_activities = activities.filter(start_time__lte=timezone.now(), end_time__gte=timezone.now())

        modules = Module.objects.filter(subject=subject)

    else:
        # For teachers, list all activities
        modules = Module.objects.filter(subject=subject)
        activities = Activity.objects.filter(subject=subject)

        finished_activities = activities.filter(
            end_time__lte=timezone.now(),
            id__in=StudentQuestion.objects.values_list('activity_question__activity_id', flat=True).distinct()
        )
        upcoming_activities = activities.filter(start_time__gt=timezone.now())
        ongoing_activities = activities.filter(start_time__lte=timezone.now(), end_time__gte=timezone.now())

    activities_with_grading_needed = []
    ungraded_items_count = 0
    if is_teacher:
        for activity in activities:
            questions_requiring_grading = ActivityQuestion.objects.filter(
                activity=activity,
                quiz_type__name__in=['Essay', 'Document']
            )
            ungraded_items = StudentQuestion.objects.filter(
                activity_question__in=questions_requiring_grading,
                status=True,
                score=0
            ).filter(
                Q(student_answer__isnull=False) | Q(uploaded_file__isnull=False)
            )
            if ungraded_items.exists():
                activities_with_grading_needed.append((activity, ungraded_items.count()))
                ungraded_items_count += ungraded_items.count()

    return render(request, 'course/viewSubjectModule.html', {
        'subject': subject,
        'modules': modules,
        'ongoing_activities': ongoing_activities,
        'upcoming_activities': upcoming_activities,
        'finished_activities': finished_activities,
        'activities_with_grading_needed': activities_with_grading_needed,
        'is_student': is_student,
        'is_teacher': is_teacher,
        'ungraded_items_count': ungraded_items_count,
        'in_current_semester': in_current_semester,
        'selected_semester': selected_semester,
        'terms': terms,
    })

# get all the finished activities
@login_required
def subjectFinishedActivities(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    user = request.user
    
    is_student = user.is_authenticated and user.profile.role.name.lower() == 'student'
    is_teacher = user.is_authenticated and user.profile.role.name.lower() == 'teacher'
    
    now = timezone.localtime(timezone.now())
    
    if is_student:
        # Get activities where the student has participated (including zero scores)
        student_activities = StudentQuestion.objects.filter(
            student=user
        ).values_list('activity_question__activity_id', flat=True).distinct()

        finished_activities = Activity.objects.filter(
            subject=subject,
            end_time__lt=now,  # Ensure the activity has ended
            id__in=student_activities
        )
    else:
        finished_activities = Activity.objects.filter(
            subject=subject,
            end_time__lt=now,  # Ensure the activity has ended
            id__in=StudentQuestion.objects.values_list('activity_question__activity_id', flat=True).distinct()
        )

    return render(request, 'course/subjectFinishedActivity.html', {
        'subject': subject,
        'finished_activities': finished_activities,
        'is_student': is_student,
        'is_teacher': is_teacher
    })


# Display the student list for a subject
@login_required
def subjectStudentList(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    
    selected_semester_id = request.GET.get('semester')
    if selected_semester_id:
        selected_semester = get_object_or_404(Semester, id=selected_semester_id)
    else:
        now = timezone.localtime(timezone.now())
        selected_semester = Semester.objects.filter(start_date__lte=now, end_date__gte=now).first()

    students = CustomUser.objects.filter(
        subjectenrollment__subject=subject,
        subjectenrollment__semester=selected_semester
    ).distinct()

    return render(request, 'course/viewStudentRoster.html', {
        'subject': subject,
        'students': students,
        'selected_semester': selected_semester, 
    })


# display subject based on semester
@login_required
def subjectList(request):
    user = request.user
    profile = get_object_or_404(Profile, user=user)
    
    # Fetch all semesters
    semesters = Semester.objects.all()

    # Determine the current semester based on the date
    current_date = timezone.now().date()
    current_semester = Semester.objects.filter(start_date__lte=current_date, end_date__gte=current_date).first()

    # Get selected semester from the dropdown
    selected_semester_id = request.GET.get('semester', None)

    # If a semester is selected, filter subjects based on the selected semester
    if selected_semester_id:
        selected_semester = get_object_or_404(Semester, id=selected_semester_id)
    else:
        selected_semester = current_semester

    # Filter subjects based on the user's role and selected semester
    if profile.role.name.lower() == 'student':
        subjects = Subject.objects.filter(
            subjectenrollment__student=user,
            subjectenrollment__semester=selected_semester
        ).distinct()
    elif profile.role.name.lower() == 'teacher':
        subjects = Subject.objects.filter(
            assign_teacher=user,
            subjectenrollment__semester=selected_semester
        ).distinct()

    return render(request, 'course/subjectList.html', {
        'subjects': subjects,
        'semesters': semesters,
        'selected_semester_id': selected_semester_id,
        'selected_semester': selected_semester, 
        'current_semester': current_semester,
    })


# Display semester list
@login_required
def semesterList(request):
    semesters = Semester.objects.all()
    form = semesterForm()
    return render(request, 'course/semester/semesterList.html', {
        'semesters': semesters, 'form': form,
    })

# Create Semester
@login_required
def createSemester(request):
    if request.method == 'POST':
        form = semesterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('semesterList')
    else:
        form = semesterForm()
    return render(request, 'course/semester/createSemester.html', {
        'form': form,
    })

# Update Semester
@login_required
def updateSemester(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if request.method == 'POST':
        form = semesterForm(request.POST, instance=semester)
        if form.is_valid():
            form.save()
            return redirect('semesterList')
    else:
        form = semesterForm(instance=semester)
    return render(request, 'course/semester/updateSemester.html', {
        'form': form, 'semester': semester
    })

# Display term list
@login_required
def termList(request):
    terms = Term.objects.all()
    return render(request, 'course/term/termList.html', {
        'terms': terms,
    })

# Create Semester
@login_required
def createTerm(request):
    if request.method == 'POST':
        form = termForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('termList')
    else:
        form = termForm()
    return render(request, 'course/term/createTerm.html', {
        'form': form,
    })

# Update Semester
@login_required
def updateTerm(request, pk):
    term = get_object_or_404(Term, pk=pk)
    if request.method == 'POST':
        form = termForm(request.POST, instance=term)
        if form.is_valid():
            form.save()
            return redirect('termList')
    else:
        form = termForm(instance=term)
    return render(request, 'course/term/updateterm.html', {
        'form': form,'term': term
    })

# Participation Scores
@login_required
def participationScoresView(request, subject_id, term_id):
    subject = get_object_or_404(Subject, id=subject_id)
    term = get_object_or_404(Term, id=term_id)
    students = CustomUser.objects.filter(subjectenrollment__subject=subject).distinct()

    max_score = request.GET.get('max_score', 100)

    if request.method == 'POST':
        for student in students:
            score_value = request.POST.get(f'score_{student.id}', '0')
            score, created = StudentParticipationScore.objects.get_or_create(
                student=student, 
                subject=subject, 
                term=term
            )
            score.score = score_value
            score.max_score = max_score
            score.save()

        return redirect('subjectDetail', pk=subject.id)

    participation_scores = StudentParticipationScore.objects.filter(subject=subject, term=term)

    return render(request, 'course/participation/createParticipation.html', {
        'subject': subject,
        'term': term,
        'students': students,
        'participation_scores': participation_scores,
        'max_score': max_score,
    })