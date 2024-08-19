from django.shortcuts import render, redirect, get_object_or_404
from .forms import subjectForm
from .models import Subject
from django.contrib.auth.decorators import login_required

# Create your views here.

#Subject List
@login_required
def subjectList(request):
    subjects = Subject.objects.all()
    return render(request, 'subject/subject.html',{'subjects': subjects})

#Create Subject
@login_required
def createSubject(request):
    if request.method == 'POST':
        form = subjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('subject')
    else:
        form = subjectForm()
    
    return render(request, 'subject/createSubject.html', {'form': form})

#Modify Subject
@login_required
def updateSubject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        form = subjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return redirect('success')
    else:
        form = subjectForm(instance=subject)
    
    return render(request, 'edit_subject.html', {'form': form})

#View Subject
@login_required
def viewSubject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    return render(request, 'view_subject.html',{'subject': subject})

#Delete Subject
@login_required
def deleteSubject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    subject.delete()
    return redirect('success')
