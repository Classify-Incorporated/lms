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
def add_course(request):
    if request.method == 'POST':
        form = courseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('success')
    else:
        form = courseForm()
    
    return render(request, 'course/add_course.html', {'form': form})

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

