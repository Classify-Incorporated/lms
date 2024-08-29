from django.shortcuts import render, redirect, get_object_or_404
from .forms import moduleForm, SCORMPackageForm
from .models import Module, SCORMPackage
from subject.models import Subject
from roles.decorators import teacher_or_admin_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .scorm_client import ScormCloud
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .scorm_client import ScormCloud
import os
import uuid
import time
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
    return render(request, 'view_module.html',{'module': module})

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
def uploadScormPackage(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)

    if request.method == 'POST':
        form = SCORMPackageForm(request.POST, request.FILES)
        if form.is_valid():
            scorm_package = form.save(commit=False)
            scorm_package.subject = subject

            # Save the SCORM package to disk first
            scorm_package.save()

            # Generate a unique course_id for SCORM Cloud
            course_id = f"{subject_id}-{uuid.uuid4()}"
            course_title = scorm_package.package_name  # Use the local package_name as the course title

            scorm_client = ScormCloud()
            result = scorm_client.import_uploaded_course(
                courseid=course_id, 
                path=scorm_package.file.path, 
                title=course_title  # Pass the title to SCORM Cloud
            )

            if 'result' in result:
                # Save the actual courseId returned by SCORM Cloud (same as the one we generated)
                scorm_package.course_id = course_id
                scorm_package.save()  # Save the updated course_id to the database
                messages.success(request, 'SCORM Package uploaded successfully and sent to SCORM Cloud!')
            else:
                messages.error(request, 'SCORM Package uploaded locally, but failed to upload to SCORM Cloud.')
            return redirect('subjectDetail', pk=subject.pk)
    else:
        form = SCORMPackageForm()

    return render(request, 'module/scorm/uploadPptx.html', {'form': form, 'subject': subject})


@login_required
@teacher_or_admin_required
def updateScormPackage(request, id):
    scorm_package = get_object_or_404(SCORMPackage, pk=id)
    subject_id = scorm_package.subject.id
    
    if request.method == 'POST':
        form = SCORMPackageForm(request.POST, request.FILES, instance=scorm_package)
        if form.is_valid():
            updated_scorm_package = form.save(commit=False)

            # Save the updated SCORM package locally first
            updated_scorm_package.save()

            # Use the existing course_id from the SCORM package
            course_id = scorm_package.course_id

            scorm_client = ScormCloud()
            result = scorm_client.import_uploaded_course(courseid=course_id, path=updated_scorm_package.file.path, may_create_new_version=True)

            if 'result' in result:
                # Save the course_id if SCORM Cloud returns the same or a new one
                updated_scorm_package.course_id = course_id
                updated_scorm_package.save()  # Save the updated course_id to the database
                messages.success(request, 'SCORM Package updated successfully and sent to SCORM Cloud!')
            else:
                messages.error(request, 'SCORM Package updated locally, but failed to update on SCORM Cloud.')
            
            return redirect('subjectDetail', pk=subject_id)
        else:
            messages.error(request, 'There was an error updating the SCORM Package. Please try again.')
    else:
        form = SCORMPackageForm(instance=scorm_package)

    return render(request, 'module/scorm/updatePptx.html', {'form': form, 'scorm_package': scorm_package})


@login_required
@teacher_or_admin_required
def deleteScormPackage(request, id):
    scorm_package = get_object_or_404(SCORMPackage, pk=id)
    subject_id = scorm_package.subject.id

    scorm_client = ScormCloud()

    # Attempt to delete the SCORM package on SCORM Cloud
    delete_result = scorm_client.delete_course(courseid=scorm_package.course_id)

    if 'error' in delete_result:
        messages.error(request, f"Failed to delete SCORM package on SCORM Cloud: {delete_result['error']}")
    else:
        messages.success(request, 'SCORM Package deleted successfully from SCORM Cloud!')

    # Delete the SCORM package locally
    scorm_package.delete()

    return redirect('subjectDetail', pk=subject_id)



@require_GET
def test_scorm_connection(request):
    scorm_client = ScormCloud()
    test_course_id = 'G7LJSUT2D88-b66d83ba-bf4c-4a1f-beb1-752875b2cd26'
    
    # Attempt to get some information about the course
    response = scorm_client.get_course_info(test_course_id)
    
    if 'error' in response:
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to connect to SCORM Cloud.',
            'error': response['error']
        }, status=500)
    else:
        return JsonResponse({
            'status': 'success',
            'message': 'Successfully connected to SCORM Cloud!',
            'data': response
        })
    
@require_GET
def list_scorm_courses(request):
    scorm_client = ScormCloud()
    response = scorm_client.list_courses()
    
    if 'error' in response:
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to retrieve course list from SCORM Cloud.',
            'error': response['error']
        }, status=500)
    else:
        return JsonResponse({
            'status': 'success',
            'message': 'Successfully retrieved course list from SCORM Cloud!',
            'data': response
        })
    

@login_required
def create_and_launch_scorm(request, scorm_id):
    scorm_package = get_object_or_404(SCORMPackage, id=scorm_id)
    course_id = scorm_package.course_id  # Use the course ID from SCORM Cloud
    scorm_client = ScormCloud()
    learner_id = request.user.id
    learner_name = request.user.get_full_name()
    registration_id = f"{learner_id}_{course_id}"
    redirect_url = request.build_absolute_uri('/dashboard/')  # Redirect URL after course completion

    # Retry mechanism for creating the registration
    registration_response = None
    for attempt in range(3):
        registration_response = scorm_client.create_registration(registration_id, course_id, learner_id, learner_name)
        if 'error' in registration_response:
            time.sleep(5)  # Wait for 5 seconds before retrying
        else:
            break  # Exit loop if registration is successful

    if 'error' in registration_response:
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to create registration for SCORM course.',
            'error': registration_response['error']
        }, status=500)
    
    # Launch the course with tracking
    launch_response = scorm_client.launch_course(registration_id, redirect_url)
    if 'error' in launch_response:
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to launch SCORM course.',
            'error': launch_response['error']
        }, status=500)
    else:
        return redirect(launch_response['launchLink'])
    

@login_required
def view_registration_data(request, registration_id):
    scorm_client = ScormCloud()
    registration_data = scorm_client.get_registration(registration_id)

    if 'error' in registration_data:
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to retrieve registration data from SCORM Cloud.',
            'error': registration_data['error']
        }, status=500)

    # Return the registration data as a JSON response
    return JsonResponse({
        'status': 'success',
        'message': 'Registration data retrieved successfully.',
        'data': registration_data
    })

@login_required
def list_registration_ids(request):
    scorm_client = ScormCloud()
    registrations = scorm_client.list_registrations()

    if 'error' in registrations:
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to retrieve list of registrations from SCORM Cloud.',
            'error': registrations['error']
        }, status=500)

    # Extract registration_ids directly from the list
    try:
        registration_ids = [registration['id'] for registration in registrations]  # Accessing list directly
    except KeyError as e:
        print(f"KeyError encountered: {e}")
        print(f"Registration data structure: {registrations}")
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to extract registration IDs: {str(e)}',
            'data': registrations  # Return the entire response for debugging
        }, status=500)
    except TypeError as e:
        print(f"TypeError encountered: {e}")
        print(f"Registration data structure: {registrations}")
        return JsonResponse({
            'status': 'error',
            'message': f'Unexpected data format: {str(e)}',
            'data': registrations  # Return the entire response for debugging
        }, status=500)

    return JsonResponse({
        'status': 'success',
        'message': 'List of registration IDs retrieved successfully.',
        'data': registration_ids
    })

@login_required
def scormRegistration(request):
    return render(request, 'module/scorm/scormRegistration.html', {})

@login_required
def detailRegistration(request, registration_id):
    return render(request, 'module/scorm/detailRegistration.html', {'registration_id': registration_id})
