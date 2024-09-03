from django.shortcuts import render, redirect, get_object_or_404
from .forms import moduleForm, SCORMPackageForm
from .models import Module, SCORMPackage, StudentProgress
from subject.models import Subject
from roles.decorators import teacher_or_admin_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET
import os
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
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
    student = request.user

    # Get or create a progress record for the student and module
    progress, created = StudentProgress.objects.get_or_create(
        student=student,
        module=module,
        defaults={'progress': 0, 'last_page': 1}
    )

    # Update the access times
    progress.save()

    context = {
        'module': module,
        'progress': progress.progress,
        'last_page': progress.last_page,
    }

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

@login_required
@csrf_exempt
def module_progress(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        module_id = data.get('module_id')
        progress_value = data.get('progress')
        last_page = data.get('last_page', 1)  # Default to 1 if not provided

        module = Module.objects.get(id=module_id)
        student = request.user

        # Retrieve the existing progress record or create a new one
        progress_record, created = StudentProgress.objects.get_or_create(
            student=student,
            module=module,
            defaults={'last_page': last_page}  # Set last_page when creating
        )

        # Print the current time spent before the update
        print(f"Before update: Total time spent: {progress_record.time_spent} seconds")

        # Calculate the time spent since the last update
        now = timezone.now()
        if progress_record.last_accessed:
            time_delta = now - progress_record.last_accessed
            added_time = int(time_delta.total_seconds())
            progress_record.time_spent += added_time

            # Print the actual time spent during this session
            print(f"Time spent this session: {added_time} seconds")

        # Update the progress and last page
        progress_record.progress = progress_value
        progress_record.last_page = last_page  # Ensure last_page is updated
        progress_record.last_accessed = now
        progress_record.save()

        # Print the total time spent after the update
        print(f"After update: Total time spent: {progress_record.time_spent} seconds")

        return JsonResponse({'status': 'success', 'progress': progress_record.progress})

    return JsonResponse({'status': 'error'}, status=400)

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
    student = request.user

    progress, created = StudentProgress.objects.get_or_create(
        student=student,
        scorm_package=scorm_package,
        defaults={'progress': 0, 'last_page': 1}
    )

    # Store the start time in session
    request.session['start_time'] = timezone.now().isoformat()

    print(f"View Scorm Package: Start Time Set in Session - {request.session['start_time']}")

    context = {
        'scorm_package': scorm_package,
        'progress': progress.progress,
        'last_page': progress.last_page,
    }

    if scorm_package.file.name.endswith('.pdf'):
        context['is_pdf'] = True
    elif scorm_package.file.name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        context['is_image'] = True
    elif scorm_package.file.name.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        context['is_video'] = True
    else:
        context['is_unknown'] = True

    return render(request, 'module/scorm/viewScormPackage.html', context)

    
@login_required
@csrf_exempt
def update_progress(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        scorm_package_id = data.get('scorm_package_id')
        progress_value = data.get('progress')
        last_page = data.get('last_page', 1)  # Default to 1 if not provided

        scorm_package = SCORMPackage.objects.get(id=scorm_package_id)
        student = request.user

        progress_record, created = StudentProgress.objects.get_or_create(
            student=student,
            scorm_package=scorm_package,
            defaults={'last_page': last_page}  # Set last_page when creating
        )

        # Get start_time from the session
        start_time_str = request.session.get('start_time')
        if start_time_str:
            start_time = timezone.datetime.fromisoformat(start_time_str)
            now = timezone.now()
            time_delta = now - start_time
            session_time_spent = int(time_delta.total_seconds())

            # Print the time spent before and after the update for debugging
            print(f"Before update: Total time spent: {progress_record.time_spent} seconds")
            print(f"Time spent this session: {session_time_spent} seconds")

            progress_record.time_spent += session_time_spent

            print(f"After update: Total time spent: {progress_record.time_spent} seconds")

            # Clear the start_time from the session after updating
            request.session['start_time'] = now.isoformat()

        # Update the progress and last page
        progress_record.progress = progress_value
        progress_record.last_page = last_page  # Ensure last_page is updated
        progress_record.last_accessed = timezone.now()
        progress_record.save()

        return JsonResponse({'status': 'success', 'progress': progress_record.progress})

    return JsonResponse({'status': 'error'}, status=400)


def progressList(request):
    student = request.user
    # Retrieve distinct SCORM packages and modules
    scorm_activities = StudentProgress.objects.filter(
        student=student, scorm_package__isnull=False
    ).select_related('scorm_package').distinct()

    module_activities = StudentProgress.objects.filter(
        student=student, module__isnull=False
    ).select_related('module').distinct()

    return render(request, 'module/progress/activityProgress.html', {
        'scorm_activities': scorm_activities,
        'module_activities': module_activities
    })

@login_required
def detailScormProgress(request, scorm_package_id):
    progress_list = StudentProgress.objects.filter(scorm_package_id=scorm_package_id)
    scorm_package = get_object_or_404(SCORMPackage, id=scorm_package_id)
    activity_name = scorm_package.package_name

    for p in progress_list:
        seconds = p.time_spent
        if seconds is not None:
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours > 0:
                p.formatted_time_spent = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                p.formatted_time_spent = f"{minutes}m {seconds}s"
            else:
                p.formatted_time_spent = f"{seconds}s"
        else:
            p.formatted_time_spent = "N/A"
    
    return render(request, 'module/progress/detailProgress.html', {
        'progress_list': progress_list,
        'activity_name': activity_name
    })

@login_required
def detailModuleProgress(request, module_id):
    progress_list = StudentProgress.objects.filter(module_id=module_id)
    module = get_object_or_404(Module, id=module_id)
    activity_name = module.file_name

    for p in progress_list:
        seconds = p.time_spent
        if seconds is not None:
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours > 0:
                p.formatted_time_spent = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                p.formatted_time_spent = f"{minutes}m {seconds}s"
            else:
                p.formatted_time_spent = f"{seconds}s"
        else:
            p.formatted_time_spent = "N/A"
    
    return render(request, 'module/progress/detailProgress.html', {
        'progress_list': progress_list,
        'activity_name': activity_name
    })