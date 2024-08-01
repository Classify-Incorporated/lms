from django.shortcuts import render, redirect, get_object_or_404
from .forms import subjectForm
from .models import Subject

# Create your views here.

#Create Subject
def createSubject(request):
    if request.method == 'POST':
        form = subjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('success')
    else:
        form = subjectForm()
    
    return render(request, 'create_subject.html', {'form': form})

#Modify Subject
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
def viewSubject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    return render(request, 'view_subject.html',{'subject': subject})

#Delete Subject
def deleteSubject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    subject.delete()
    return redirect('success')
