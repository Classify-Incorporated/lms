from django.shortcuts import render, redirect, get_object_or_404
from .forms import courseForm, sectionForm
from .models import Course, SubjectEnrollment, Semester, Section
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


def courseList(request):
    form = courseForm()
    user = request.user

    if user.profile.role.name.lower() == 'student':
        courses = Course.objects.filter(section__subjects__subjectenrollment__student=user).distinct()
    elif user.profile.role.name.lower() == 'teacher':
        courses = Course.objects.filter(section__subjects__assign_teacher=user).distinct()
    else:
        courses = Course.objects.all()

    selected_course = None
    subjects = []
    faculty = []

    if 'course_id' in request.GET:
        selected_course = get_object_or_404(Course, pk=request.GET['course_id'])

        if user.profile.role.name.lower() == 'student':
            subjects = Subject.objects.filter(subjectenrollment__student=user, section__course=selected_course).distinct()
        else:
            subjects = Subject.objects.filter(section__course=selected_course).distinct()

        faculty = CustomUser.objects.filter(section__subjects__in=subjects, profile__role__name__iexact='teacher').distinct()

    return render(request, 'course/course.html', {
        'courses': courses,
        'form': form,
        'selected_course': selected_course,
        'subjects': subjects,
        'faculty': faculty
    })

def viewCourse(request, pk):
    course = get_object_or_404(Course, pk=pk)
    user = request.user
    
    if user.profile.role.name.lower() == 'student':
        subjects = Subject.objects.filter(subjectenrollment__student=user, section__course=course).distinct()
    else:
        subjects = Subject.objects.filter(section__course=course).distinct()
    
    faculty = CustomUser.objects.filter(subject__in=subjects, profile__role__name__iexact='teacher').distinct()
    
    html_content = render_to_string('course/viewCourse.html', {
        'course': course,
        'subjects': subjects,
        'faculty': faculty
    })

    return JsonResponse({
        'course_name': course.course_name,
        'html_content': html_content
    })



#Create Course
def addCourse(request):
    if request.method == 'POST':
        form = courseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('courseList')
    else:
        form = courseForm()
    
    return render(request, 'course/course.html', {'form': form})

#Modify Course
def updateCourse(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = courseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('courseList')
    else:
        form = courseForm(instance=course)
    
    return render(request, 'edit_role.html', {'form': form})



# Handle the enrollment of regular students
class EnrollRegularStudentView(View):
    def get(self, request, *args, **kwargs):
        profiles = Profile.objects.filter(role__name__iexact='student', student_status='Regular')
        courses = Course.objects.all()
        semesters = Semester.objects.all()
        
        return render(request, 'course/subjectEnrollment/addRegularStudent.html', {
            'profiles': profiles,
            'courses': courses,
            'semesters': semesters
        })
    
    def post(self, request, *args, **kwargs):
        student_profile_id = request.POST.get('student_profile')
        course_id = request.POST.get('course_id')
        semester_id = request.POST.get('semester_id')
        
        student_profile = get_object_or_404(Profile, id=student_profile_id)
        student = student_profile.user
        course = get_object_or_404(Course, id=course_id)
        semester = get_object_or_404(Semester, id=semester_id)
        
        # Fetch subjects related to the course
        subjects = Subject.objects.filter(section__course=course)
        
        subject_enrollment, created = SubjectEnrollment.objects.get_or_create(student=student, semester=semester)
        subject_enrollment.subjects.add(*subjects)
        
        return JsonResponse({
            'message': f'Student {student.email} enrolled in course {course.course_name} for {semester.semester_name} successfully.',
            'enrolled_subjects': [subject.subject_name for subject in subjects]
        })

# Handle the enrollment of irregular students
class EnrollIrregularStudentView(View):
    def get(self, request, *args, **kwargs):
        profiles = Profile.objects.filter(role__name__iexact='student', student_status='Irregular')
        subjects = Subject.objects.all()
        semesters = Semester.objects.all()
        
        return render(request, 'course/subjectEnrollment/addIrregularStudent.html', {
            'profiles': profiles,
            'subjects': subjects,
            'semesters': semesters
        })
    
    def post(self, request, *args, **kwargs):
        student_profile_id = request.POST.get('student_profile')
        subject_ids = request.POST.getlist('subject_ids')
        semester_id = request.POST.get('semester_id')
        
        student_profile = get_object_or_404(Profile, id=student_profile_id)
        student = student_profile.user
        subjects = Subject.objects.filter(id__in=subject_ids)
        semester = get_object_or_404(Semester, id=semester_id)
        
        subject_enrollment, created = SubjectEnrollment.objects.get_or_create(student=student, semester=semester)
        subject_enrollment.subjects.add(*subjects)
        
        return JsonResponse({
            'message': f'Student {student.email} enrolled successfully for {semester.semester_name}.',
            'enrolled_subjects': [subject.subject_name for subject in subjects]
        })
    

#add Regular Student
def addRegularStudent(request):
    student_role = Role.objects.get(name__iexact='student')
    profiles = Profile.objects.filter(role=student_role, student_status__iexact='Regular')
    courses = Course.objects.all()
    semesters = Semester.objects.all()

    profiles_json = json.dumps(list(profiles.values('id', 'first_name', 'last_name', 'student_status')), cls=DjangoJSONEncoder)
    
    return render(request, 'course/subjectEnrollment/addRegularStudent.html', {
        'profiles': profiles,
        'profiles_json': profiles_json,
        'courses': courses,
        'semesters': semesters,
    })

# add Irregular Student
def addIrregularStudent(request):
    student_role = Role.objects.get(name__iexact='student')
    profiles = Profile.objects.filter(role=student_role, student_status__iexact='Irregular')
    subjects = Subject.objects.all()
    semesters = Semester.objects.all()

    profiles_json = json.dumps(list(profiles.values('id', 'first_name', 'last_name', 'student_status')), cls=DjangoJSONEncoder)
    
    return render(request, 'course/subjectEnrollment/addIrregularStudent.html', {
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
    
    if is_student:
        completed_activities = StudentQuestion.objects.filter(student=user, score__gt=0).values_list('activity_question__activity_id', flat=True).distinct()
        answered_essays = StudentQuestion.objects.filter(student=user, activity_question__quiz_type__name='Essay', student_answer__isnull=False).values_list('activity_question__activity_id', flat=True).distinct()
        activities = Activity.objects.filter(subject=subject).exclude(id__in=completed_activities.union(answered_essays))
        finished_activities = Activity.objects.filter(subject=subject, id__in=completed_activities.union(answered_essays))
        modules = Module.objects.filter(subject=subject)
    else:
        modules = Module.objects.filter(subject=subject)
        activities = Activity.objects.filter(subject=subject)
        finished_activities = Activity.objects.filter(subject=subject, id__in=StudentQuestion.objects.values_list('activity_question__activity_id', flat=True).distinct())
    
    activities_with_essays = set()
    ungraded_essay_count = 0
    if is_teacher:
        for activity in activities:
            if ActivityQuestion.objects.filter(activity=activity, quiz_type__name='Essay').exists():
                activities_with_essays.add(activity.id)
                ungraded_essay_count += StudentQuestion.objects.filter(activity_question__activity=activity, activity_question__quiz_type__name='Essay', status=False).count()
    
    html_content = render_to_string('course/viewSubjectModule.html', {
        'subject': subject,
        'modules': modules,
        'activities': activities,
        'finished_activities': finished_activities,
        'activities_with_essays': activities_with_essays,
        'is_student': is_student,
        'is_teacher': is_teacher,
        'ungraded_essay_count': ungraded_essay_count
    })

    return JsonResponse({
        'subject_name': subject.subject_name,
        'html_content': html_content
    })


# Display course list
def courseStudentList(request, pk):
    course = get_object_or_404(Course, pk=pk)
    students = CustomUser.objects.filter(subjectenrollment__subjects__section__course=course).distinct()

    regular_students = students.filter(profile__student_status='Regular')
    irregular_students = students.filter(profile__student_status='Irregular')

    return render(request, 'course/studentRoster.html', {
        'course': course,
        'regular_students': regular_students,
        'irregular_students': irregular_students,
    })

#Display Section
def sectionList(request):
    sections = Section.objects.all()
    return render(request, 'course/section/sectionList.html', {'sections': sections})


# Create sections
def createSection(request):
    form = sectionForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            section = form.save()
            print('created successfully.')
            return redirect('sectionList') 
    else:
        form = sectionForm()
    
    return render(request, 'course/section/createSection.html', {'form': form})

# Update sections
def updateSection(request, id):
    section = get_object_or_404(Section, id=id)
    if request.method == 'POST':
        form = sectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            return redirect('sectionList')
    else:
        form = sectionForm(instance=section)
    return render(request, 'course/section/updateSection.html', {'form': form, 'section': section})
    