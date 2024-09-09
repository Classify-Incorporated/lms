from django.shortcuts import render, redirect, get_object_or_404
from .forms import moduleForm
from .models import Module, StudentProgress
from subject.models import Subject
from roles.decorators import teacher_or_admin_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import os
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from course.models import Semester
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
# Create your views here.

#Module List
@login_required
@permission_required('module.view_module', raise_exception=True)
def moduleList(request):
    modules = Module.objects.all()
    return render(request, 'module/module.html',{'modules': modules})

#Create Module
@login_required
@permission_required('module.add_module', raise_exception=True)
def createModule(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    
    now = timezone.localtime(timezone.now())
    current_semester = Semester.objects.filter(start_date__lte=now, end_date__gte=now).first()
    
    if request.method == 'POST':
        form = moduleForm(request.POST, request.FILES, current_semester=current_semester)
        if form.is_valid():
            module = form.save(commit=False)
            module.subject = subject
            module.save()
            
            form.save_m2m()  # Save many-to-many data for selected users

            messages.success(request, 'Module created successfully!')
            return redirect('subjectDetail', pk=subject_id)
        else:
            messages.error(request, 'There was an error creating the module. Please try again.')
    else:
        form = moduleForm(current_semester=current_semester)

    return render(request, 'module/createModule.html', {'form': form, 'subject': subject})

#Modify Module
@login_required
@permission_required('module.change_module', raise_exception=True)
def updateModule(request, pk):
    module = get_object_or_404(Module, pk=pk)
    subject_id = module.subject.id

    now = timezone.localtime(timezone.now())
    current_semester = Semester.objects.filter(start_date__lte=now, end_date__gte=now).first()

    if request.method == 'POST':
        form = moduleForm(request.POST, request.FILES, instance=module, current_semester=current_semester)
        if form.is_valid():
            form.save()
            messages.success(request, 'Module updated successfully!')
            return redirect('subjectDetail', pk=subject_id)
        else:
            messages.error(request, 'There was an error updating the module. Please try again.')
    else:
        form = moduleForm(instance=module, current_semester=current_semester)

    return render(request, 'module/updateModule.html', {'form': form, 'module': module})


#View Module
@login_required
@permission_required('module.view_module', raise_exception=True)
def viewModule(request, pk):
    module = get_object_or_404(Module, pk=pk)
    student = request.user

    # Get or create a progress record for the student and module
    progress, created = StudentProgress.objects.get_or_create(
        student=student,
        module=module,
        defaults={'progress': 0, 'last_page': 1}
    )

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

        now = timezone.now()

        # Calculate the time spent since the last update, but only if the session was active
        if progress_record.last_accessed and request.session.get('is_active', False):
            time_delta = now - progress_record.last_accessed
            added_time = int(time_delta.total_seconds())
            progress_record.time_spent += added_time
            request.session['is_active'] = False  # Deactivate session

        # Update progress, last page, and last access time
        progress_record.progress = progress_value
        progress_record.last_page = last_page
        progress_record.last_accessed = now
        progress_record.save()

        return JsonResponse({'status': 'success', 'progress': progress_record.progress})

    return JsonResponse({'status': 'error'}, status=400)

def start_module_session(request):
    """
    This view will be triggered when a student opens a module.
    It will mark the start of an active session.
    """
    if request.method == 'POST':
        request.session['is_active'] = True  # Mark session as active
        return JsonResponse({'status': 'session started'})

def stop_module_session(request):
    """
    This view will be triggered when a student stops the module.
    It will mark the end of an active session.
    """
    if request.method == 'POST':
        request.session['is_active'] = False  # Mark session as inactive
        return JsonResponse({'status': 'session stopped'})

#Delete Module
@login_required
@teacher_or_admin_required
@permission_required('module.delete_module', raise_exception=True)
def deleteModule(request, pk):
    module = get_object_or_404(Module, pk=pk)
    subject_id = module.subject.id
    messages.success(request, 'Module deleted successfully!')
    module.delete()
    return redirect('subjectDetail', pk=subject_id)

@login_required
def progressList(request):
    student = request.user
    
    module_activities = StudentProgress.objects.filter(
        student=student, module__isnull=False
    ).select_related('module').distinct()

    return render(request, 'module/progress/activityProgress.html', {
        'module_activities': module_activities
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

@login_required
def download_module(request, module_id):
    # Get the module object
    module = get_object_or_404(Module, pk=module_id)

    if not module.file:
        return HttpResponse("No file available for download.", status=404)

    # Open the file in binary mode
    file_path = module.file.path  # Assuming your Module model has a file field or similar
    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type="application/octet-stream")
        response['Content-Disposition'] = f'attachment; filename="{module.file_name}"'
        return response