from django.shortcuts import render, redirect, get_object_or_404
from .models import SubjectEnrollment, Semester, Term
from accounts.models import Profile
from subject.models import Subject
from roles.models import Role
from module.models import Module
from activity.models import Activity ,StudentQuestion, ActivityQuestion
from django.views import View
from django.http import JsonResponse
import json
from django.core.serializers.json import DjangoJSONEncoder
from accounts.models import CustomUser
from django.template.loader import render_to_string
from django.utils import timezone
from .forms import semesterForm, termForm
from django.db.models import Q

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

        
        return JsonResponse({
            'message': f'Student {student.email} enrolled successfully for {semester.semester_name}.',
        })



# Add Irregular Student
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
def subjectDetail(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    user = request.user
    
    is_student = user.is_authenticated and user.profile.role.name.lower() == 'student'
    is_teacher = user.is_authenticated and user.profile.role.name.lower() == 'teacher'
    
    now = timezone.localtime(timezone.now())
    
    if is_student:
        completed_activities = StudentQuestion.objects.filter(student=user, score__gt=0).values_list('activity_question__activity_id', flat=True).distinct()
        answered_essays_and_documents = StudentQuestion.objects.filter(
            student=user,
            activity_question__quiz_type__name__in=['Essay', 'Document']
        ).filter(
            Q(student_answer__isnull=False) | Q(uploaded_file__isnull=False)
        ).values_list('activity_question__activity_id', flat=True).distinct()
        activities = Activity.objects.filter(subject=subject).exclude(id__in=completed_activities.union(answered_essays_and_documents))
        finished_activities = Activity.objects.filter(subject=subject, id__in=completed_activities.union(answered_essays_and_documents))
        upcoming_activities = activities.filter(start_time__gt=now)
        ongoing_activities = activities.filter(start_time__lte=now, end_time__gte=now)
        modules = Module.objects.filter(subject=subject)
    else:
        modules = Module.objects.filter(subject=subject)
        activities = Activity.objects.filter(subject=subject)
        finished_activities = Activity.objects.filter(subject=subject, id__in=StudentQuestion.objects.values_list('activity_question__activity_id', flat=True).distinct())
        upcoming_activities = activities.filter(start_time__gt=now)
        ongoing_activities = activities.filter(start_time__lte=now, end_time__gte=now)
    
    activities_with_grading_needed = []
    ungraded_items_count = 0
    if is_teacher:
        for activity in activities:
            questions_requiring_grading = ActivityQuestion.objects.filter(
                activity=activity,
                quiz_type__name__in=['Essay', 'Document']
            )
            ungraded_items = StudentQuestion.objects.filter(
                Q(activity_question__in=questions_requiring_grading),
                Q(student_answer__isnull=False) | Q(uploaded_file__isnull=False),
                status=False  # Only include ungraded submissions
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
        'ungraded_items_count': ungraded_items_count
    })

# get all the finished activities
def finishedActivities(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    user = request.user
    
    is_student = user.is_authenticated and user.profile.role.name.lower() == 'student'
    is_teacher = user.is_authenticated and user.profile.role.name.lower() == 'teacher'
    
    if is_student:
        completed_activities = StudentQuestion.objects.filter(student=user, score__gt=0).values_list('activity_question__activity_id', flat=True).distinct()
        answered_essays = StudentQuestion.objects.filter(student=user, activity_question__quiz_type__name='Essay', student_answer__isnull=False).values_list('activity_question__activity_id', flat=True).distinct()
        finished_activities = Activity.objects.filter(subject=subject, id__in=completed_activities.union(answered_essays))
    else:
        finished_activities = Activity.objects.filter(subject=subject, id__in=StudentQuestion.objects.values_list('activity_question__activity_id', flat=True).distinct())

    return render(request, 'course/subjectFinishedActivity.html', {
        'subject': subject,
        'finished_activities': finished_activities,
        'is_student': is_student,
        'is_teacher': is_teacher
    })


# Display the student list for a subject
def subjectStudentList(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    students = CustomUser.objects.filter(subjectenrollment__subjects=subject).distinct()

    regular_students = students.filter(profile__student_status='Regular')
    irregular_students = students.filter(profile__student_status='Irregular')

    return render(request, 'course/studentRoster.html', {
        'subject': subject,
        'regular_students': regular_students,
        'irregular_students': irregular_students,
    })



def subjectList(request):
    user = request.user
    profile = get_object_or_404(Profile, user=user)
    subjects = []

    if profile.role.name.lower() == 'student':
        subjects = Subject.objects.filter(subjectenrollment__student=user).distinct()
    elif profile.role.name.lower() == 'teacher':
        subjects = Subject.objects.filter(assign_teacher=user).distinct()

    return render(request, 'course/subjectList.html', {
        'subjects': subjects,
    })

# Display semester list
def semesterList(request):
    semesters = Semester.objects.all()
    return render(request, 'course/semester/semesterList.html', {
        'semesters': semesters,
    })

# Create Semester
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
def updateSemeter(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if request.method == 'POST':
        form = semesterForm(request.POST, instance=semester)
        if form.is_valid():
            form.save()
            return redirect('semesterList')
    else:
        form = semesterForm(instance=semester)
    return render(request, 'course/semester/updateSemester.html', {
        'form': form,'semester': semester
    })

# Display term list
def termList(request):
    terms = Term.objects.all()
    return render(request, 'course/term/termList.html', {
        'terms': terms,
    })

# Create Semester
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


