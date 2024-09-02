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

            # Save the package to disk first
            package.save()

            # Handle the .zip file and extract images (if applicable)
            if package.file.name.endswith('.zip'):
                package.image_paths = package.extract_images_from_zip()
                package.save(update_fields=['image_paths'])

            # Handle the .pptx file (using Aspose.Slides)
            elif package.file.name.endswith('.pptx'):
                package.image_paths = package.convert_pptx_to_images()
                package.save(update_fields=['image_paths'])

            # Handle the .pdf file
            elif package.file.name.endswith('.pdf'):
                package.pdf_pages = package.convert_pdf_to_images(package.file.path)
                package.save(update_fields=['pdf_pages'])

            messages.success(request, f'{package.package_name} uploaded successfully and processed!')
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

            # Save the updated package locally first
            updated_package.save()

            # Handle different file types
            if updated_package.file.name.endswith('.pptx'):
                updated_package.image_paths = updated_package.convert_pptx_to_images()
            elif updated_package.file.name.endswith('.pdf'):
                updated_package.pdf_pages = updated_package.convert_pdf_to_images()
            elif updated_package.file.name.endswith(('.mp4', '.avi', '.mov')):
                updated_package.video_paths = [updated_package.file.url]  # Store video URL for streaming

            updated_package.save(update_fields=['image_paths', 'pdf_pages', 'video_paths'])

            messages.success(request, f'{updated_package.package_name} updated successfully and processed!')
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

    if package.image_paths:
        for image_path in package.image_paths:
            if os.path.exists(image_path):
                os.remove(image_path)

    if package.pdf_pages:
        for pdf_page in package.pdf_pages:
            if os.path.exists(pdf_page):
                os.remove(pdf_page)

    if package.video_paths:
        for video_path in package.video_paths:
            video_full_path = os.path.join(settings.MEDIA_ROOT, video_path)
            if os.path.exists(video_full_path):
                os.remove(video_full_path)

    # Delete the package locally
    package.delete()
    messages.success(request, 'Package deleted successfully!')

    return redirect('subjectDetail', pk=subject_id)




@login_required
def view_scorm_package(request, id):
    scorm_package = get_object_or_404(SCORMPackage, pk=id)
    
    # Correcting the file paths by replacing backslashes with forward slashes
    image_paths = [settings.MEDIA_URL + path.replace('\\', '/') for path in scorm_package.image_paths]
    
    return render(request, 'module/scorm/viewScormPackage.html', {
        'scorm_package': scorm_package,
        'image_paths': image_paths,
    })

    




