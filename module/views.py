from django.shortcuts import render, redirect, get_object_or_404
from .forms import moduleForm
from .models import Module
from subject.models import Subject
# Create your views here.

#Module List
def moduleList(request):
    modules = Module.objects.all()
    return render(request, 'module/module.html',{'modules': modules})

#Create Module
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
def viewModule(request, pk):
    module = get_object_or_404(Module, pk=pk)
    return render(request, 'view_module.html',{'module': module})

#Delete Module
def deleteModule(request, pk):
    module = get_object_or_404(Module, pk=pk)
    module.delete()
    return redirect('success')

