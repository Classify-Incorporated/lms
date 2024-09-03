from django.shortcuts import render, redirect, get_object_or_404
from .forms import moduleForm, SCORMPackageForm
from .models import Module, SCORMPackage
from subject.models import Subject
from roles.decorators import teacher_or_admin_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET
import os

# Create your views here.

#Module List
@login_required
@teacher_or_admin_required
def moduleList(request):
    modules = Module.objects.all()
    return render(request, 'module/module.html',{'modules': modules})

#Create Module
@login_required
@teacher_or_admin_required
def createModule(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        form = moduleForm(request.POST, request.FILES)  
        if form.is_valid():
            module = form.save(commit=False)
            module.subject = subject  
            module.save()
            messages.success(request, 'Module created successfully!')
            return redirect('subjectDetail', pk=subject_id)
        else:
            messages.error(request, 'There was an error creating the module. Please try again.')
    else:
        form = moduleForm()

    return render(request, 'module/createModule.html', {'form': form, 'subject': subject})

#Modify Module
@login_required
@teacher_or_admin_required
def updateModule(request, pk):
    module = get_object_or_404(Module, pk=pk)
    subject_id = module.subject.id
    if request.method == 'POST':
        form = moduleForm(request.POST, instance=module)
        if form.is_valid():
            form.save()
            messages.success(request, 'Module updated successfully!')
            return redirect('subjectDetail', pk=subject_id)
        else:
            messages.error(request, 'There was an error updated the module. Please try again.')
    else:
        form = moduleForm(instance=module)
    
    return render(request, 'module/updateModule.html', {'form': form,'module':module })

#View Module
@login_required
@teacher_or_admin_required
def viewModule(request, pk):
    module = get_object_or_404(Module, pk=pk)
    context = {'module': module}

    # Determine the file type and prepare context accordingly
    if module.file.name.endswith('.pdf'):
        context['is_pdf'] = True
    elif module.file.name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        context['is_image'] = True
    elif module.file.name.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        context['is_video'] = True
    else:
        context['is_unknown'] = True

    return render(request, 'module/viewModule.html', context)

#Delete Module
@login_required
@teacher_or_admin_required
def deleteModule(request, pk):
    module = get_object_or_404(Module, pk=pk)
    subject_id = module.subject.id
    messages.success(request, 'Module deleted successfully!')
    module.delete()
    return redirect('subjectDetail', pk=subject_id)


@login_required
@teacher_or_admin_required
def uploadPackage(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)

    if request.method == 'POST':
        form = SCORMPackageForm(request.POST, request.FILES)
        if form.is_valid():
            package = form.save(commit=False)
            package.subject = subject
            package.save()

            messages.success(request, f'{package.package_name} uploaded successfully!')
            return redirect('subjectDetail', pk=subject.pk)
    else:
        form = SCORMPackageForm()

    return render(request, 'module/scorm/createScorm.html', {'form': form, 'subject': subject})


@login_required
@teacher_or_admin_required
def updatePackage(request, id):
    package = get_object_or_404(SCORMPackage, pk=id)
    subject_id = package.subject.id

    if request.method == 'POST':
        form = SCORMPackageForm(request.POST, request.FILES, instance=package)
        if form.is_valid():
            updated_package = form.save(commit=False)
            updated_package.save()
            messages.success(request, f'{updated_package.package_name} updated successfully!')
            return redirect('subjectDetail', pk=subject_id)
        else:
            messages.error(request, 'There was an error updating the package. Please try again.')
    else:
        form = SCORMPackageForm(instance=package)

    return render(request, 'module/scorm/updatePptx.html', {'form': form, 'package': package})


@login_required
@teacher_or_admin_required
def deletePackage(request, id):
    package = get_object_or_404(SCORMPackage, pk=id)
    subject_id = package.subject.id

    if package.file:
        if os.path.exists(package.file.path):
            os.remove(package.file.path)

    package.delete()
    messages.success(request, 'Package deleted successfully!')

    return redirect('subjectDetail', pk=subject_id)


@login_required
def viewScormPackage(request, id):
    scorm_package = get_object_or_404(SCORMPackage, pk=id)
    context = {'scorm_package': scorm_package}

    # Determine the file type and prepare context accordingly
    if scorm_package.file.name.endswith('.pdf'):
        context['is_pdf'] = True
    elif scorm_package.file.name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        context['is_image'] = True
    elif scorm_package.file.name.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        context['is_video'] = True
    else:
        context['is_unknown'] = True

    return render(request, 'module/scorm/viewScormPackage.html', context)

    




