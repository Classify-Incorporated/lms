from django.shortcuts import render, redirect, get_object_or_404
from .forms import courseForm
from .models import Course, SubjectEnrollment
from accounts.models import Profile
from subject.models import Subject
from roles.models import Role
from django.views import View
from django.http import JsonResponse
import json
from django.core.serializers.json import DjangoJSONEncoder
from accounts.models import CustomUser
# Create your views here.

#Course List
def courseList(request):
    form = courseForm()
    courses = Course.objects.all()
    selected_course = None
    faculty = []
    if 'course_id' in request.GET:
        selected_course = get_object_or_404(Course, pk=request.GET['course_id'])
        # Get all assigned teachers for the selected course
        faculty = CustomUser.objects.filter(subject__course=selected_course).distinct()

    return render(request, 'course/course.html', {'courses': courses, 'form': form, 'selected_course': selected_course, 'faculty': faculty})


#Create Course
def add_course(request):
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

#View Course
def viewCourse(request, pk):
    course = get_object_or_404(Course, pk=pk)
    return render(request, 'course/course.html',{'course': course})

#Handle the enrollment of regular students
class EnrollRegularStudentView(View):
    def get(self, request, *args, **kwargs):
        profiles = Profile.objects.filter(role__name__iexact='student', student_status='Regular')
        courses = Course.objects.all()
        
        return render(request, 'course/enrollRegularStudent.html', {
            'profiles': profiles,
            'courses': courses
        })
    
    def post(self, request, *args, **kwargs):
        student_profile_id = request.POST.get('student_profile')
        course_id = request.POST.get('course_id')
        
        student_profile = get_object_or_404(Profile, id=student_profile_id)
        student = student_profile.user
        course = get_object_or_404(Course, id=course_id)
        subjects = course.subjects.all()
        
        subject_enrollment, created = SubjectEnrollment.objects.get_or_create(student=student)
        subject_enrollment.subjects.add(*subjects)
        
        return JsonResponse({
            'message': f'Student {student.email} enrolled in course {course.course_name} successfully.',
            'enrolled_subjects': [subject.subject_name for subject in subjects]
        })


#Handle the enrollment of irregular students
class EnrollIrregularStudentView(View):
    def get(self, request, *args, **kwargs):
        profiles = Profile.objects.filter(role__name__iexact='student', student_status='Irregular')
        subjects = Subject.objects.all()
        
        return render(request, 'course/enrollIrregularStudent.html', {
            'profiles': profiles,
            'subjects': subjects
        })
    
    def post(self, request, *args, **kwargs):
        student_profile_id = request.POST.get('student_profile')
        subject_ids = request.POST.getlist('subject_ids')
        
        student_profile = get_object_or_404(Profile, id=student_profile_id)
        student = student_profile.user
        subjects = Subject.objects.filter(id__in=subject_ids)
        
        subject_enrollment, created = SubjectEnrollment.objects.get_or_create(student=student)
        subject_enrollment.subjects.add(*subjects)
        
        return JsonResponse({
            'message': f'Student {student.email} enrolled successfully.',
            'enrolled_subjects': [subject.subject_name for subject in subjects]
        })

def add_regular_student(request):
    student_role = Role.objects.get(name__iexact='student')
    profiles = Profile.objects.filter(role=student_role, student_status__iexact='Regular')
    courses = Course.objects.all()

    profiles_json = json.dumps(list(profiles.values('id', 'first_name', 'last_name', 'student_status')), cls=DjangoJSONEncoder)
    
    return render(request, 'course/addRegularStudent.html', {
        'profiles': profiles,
        'profiles_json': profiles_json,
        'courses': courses,
    })

def add_irregular_student_course(request):
    student_role = Role.objects.get(name__iexact='student')
    profiles = Profile.objects.filter(role=student_role, student_status__iexact='Irregular')
    subjects = Subject.objects.all()

    profiles_json = json.dumps(list(profiles.values('id', 'first_name', 'last_name', 'student_status')), cls=DjangoJSONEncoder)
    
    return render(request, 'course/addIrregularStudent.html', {
        'profiles': profiles,
        'profiles_json': profiles_json,
        'subjects': subjects
    })

#sample