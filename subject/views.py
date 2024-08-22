from django.shortcuts import render, redirect, get_object_or_404
from .forms import subjectForm
from .models import Subject
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# Create your views here.

#Subject List
@login_required
def subjectList(request):
    if request.user.profile.role.name.lower() == 'teacher':
        subjects = Subject.objects.filter(assign_teacher=request.user)
    else:
        subjects = Subject.objects.all()

    form = subjectForm()
    return render(request, 'subject/subject.html', {'subjects': subjects, 'form': form})

#Create Subject
@login_required
def createSubject(request):
    if request.method == 'POST':
        form = subjectForm(request.POST, request.FILES)
        if form.is_valid():
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
def deleteSubject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    subject.delete()
    messages.success(request, 'Subject deleted successfully!')
    return redirect('subject')
