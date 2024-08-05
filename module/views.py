from django.shortcuts import render, redirect, get_object_or_404
from .forms import moduleForm
from .models import Module
# Create your views here.

#Module List
def moduleList(request):
    modules = Module.objects.all()
    return render(request, 'module/module.html',{'modules': modules})

#Create Module
def createModule(request):
    if request.method == 'POST':
        form = moduleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('success')
    else:
        form = moduleForm()
    
    return render(request, 'create_module.html', {'form': form})

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

