from django.shortcuts import render, redirect, get_object_or_404
from .forms import courseForm
from .models import Course
# Create your views here.

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
    return render(request, 'view_role.html',{'course': course})


