from django.shortcuts import render, redirect, get_object_or_404
from .forms import moduleForm
from .models import Module
from subject.models import Subject
from roles.decorators import teacher_required, student_required
from django.contrib.auth.decorators import login_required
# Create your views here.

#Module List
@login_required
@teacher_required
@student_required
def moduleList(request):
    modules = Module.objects.all()
    return render(request, 'module/module.html',{'modules': modules})

#Create Module
@login_required
@teacher_required
def createModule(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        form = moduleForm(request.POST, request.FILES)  
        if form.is_valid():
            module = form.save(commit=False)
            module.subject = subject  
            module.save()
            return redirect('subjectDetail', pk=subject_id)
    else:
        form = moduleForm()

    return render(request, 'module/createModule.html', {'form': form, 'subject': subject})

#Modify Module
@login_required
@teacher_required
def updateModule(request, pk):
    module = get_object_or_404(Module, pk=pk)
    if request.method == 'POST':
        form = moduleForm(request.POST, instance=module)
        if form.is_valid():
            form.save()
            return redirect('success')
    else:
        form = moduleForm(instance=module)
    
    return render(request, 'edit_module.html', {'form': form})

#View Module
@login_required
@teacher_required
def viewModule(request, pk):
    module = get_object_or_404(Module, pk=pk)
    return render(request, 'view_module.html',{'module': module})

#Delete Module
@login_required
@teacher_required
def deleteModule(request, pk):
    module = get_object_or_404(Module, pk=pk)
    module.delete()
    return redirect('success')

