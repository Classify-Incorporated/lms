from django.shortcuts import render, redirect, get_object_or_404
from .forms import courseForm
from .models import Course, SubjectEnrollment
from accounts.models import Profile
from subject.models import Subject
from django.views import View
from django.http import JsonResponse
# Create your views here.

#Course List
def courseList(request):
    courses = Course.objects.all()
    return render(request, 'course/course.html',{'courses': courses})

#Create Course
def createCourse(request):
    if request.method == 'POST':
        form = courseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('success')
    else:
        form = courseForm()
    
    return render(request, 'create_role.html', {'form': form})

#Modify Course
def updateCourse(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = courseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('success')
    else:
        form = courseForm(instance=course)
    
    return render(request, 'edit_role.html', {'form': form})

#View Course
def viewCourse(request, pk):
    course = get_object_or_404(Course, pk=pk)
    return render(request, 'course/view_course.html',{'course': course})

#Handle the enrollment of regular students and irregular students
class EnrollStudentView(View):
    def get(self, request, *args, **kwargs):
        profiles = Profile.objects.all()
        courses = Course.objects.all()
        subjects = Subject.objects.all()
        
        # Debug prints
        print("Profiles: ", profiles)
        print("Courses: ", courses)
        print("Subjects: ", subjects)
        
        return render(request, 'enroll_student.html', {
            'profiles': profiles,
            'courses': courses,
            'subjects': subjects
        })
    
    def post(self, request, *args, **kwargs):
        student_profile_id = request.POST.get('student_profile')
        course_id = request.POST.get('course_id')
        subject_ids = request.POST.getlist('subject_ids')
        
        student_profile = get_object_or_404(Profile, id=student_profile_id)
        student = student_profile.user
        
        if course_id:
            course = get_object_or_404(Course, id=course_id)
            subjects = course.subjects.all()
        else:
            subjects = Subject.objects.filter(id__in=subject_ids)
        
        subject_enrollment, created = SubjectEnrollment.objects.get_or_create(student=student)
        subject_enrollment.subjects.add(*subjects)
        
        return JsonResponse({
            'message': f'Student {student.email} enrolled successfully.',
            'enrolled_subjects': [subject.subject_name for subject in subjects]
        })
    

def add_student_course(request):
    profiles = Profile.objects.all()
    courses = Course.objects.all()
    subjects = Subject.objects.all()
    
    return render(request, 'course/add_student_course.html', {
        'profiles': profiles,
        'courses': courses,
        'subjects': subjects
    })