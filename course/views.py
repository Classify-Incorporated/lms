from django.shortcuts import render, redirect, get_object_or_404
from .models import SubjectEnrollment, Semester, Term, Retake
from accounts.models import Profile
from subject.models import Subject
from roles.models import Role
from module.models import Module
from activity.models import Activity ,StudentQuestion, ActivityQuestion
from django.views import View
from django.core.serializers.json import DjangoJSONEncoder
from accounts.models import CustomUser
from django.utils import timezone
from .forms import *
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django import forms
from django.http import HttpResponse
from module.forms import moduleForm
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required
from .utils import copy_activities_from_previous_semester
from datetime import date
from django.utils.dateformat import DateFormat
from datetime import datetime
from django.db.models import ProtectedError
from django.db.models import Avg
from module.models import StudentProgress
from activity.models import ActivityType
from django.views.decorators.csrf import csrf_exempt
from .msteams_utils import create_teams_meeting
import json
from django.http import JsonResponse, HttpResponseBadRequest
from collections import defaultdict


# Handle the enrollment of students
@method_decorator(login_required, name='dispatch')
class enrollStudentView(View):
    def post(self, request, *args, **kwargs):
        student_profile_ids = request.POST.getlist('student_profile')
        subject_ids = request.POST.getlist('subject_ids')
        semester_id = request.POST.get('semester_id')

        semester = get_object_or_404(Semester, id=semester_id)
        duplicate_enrollments = []

        # Loop through selected students and enroll them in the subjects
        for student_profile_id in student_profile_ids:
            student_profile = get_object_or_404(Profile, id=student_profile_id)
            student = student_profile.user
            subjects = Subject.objects.filter(id__in=subject_ids)

            for subject in subjects:
                subject_enrollment, created = SubjectEnrollment.objects.get_or_create(
                    student=student,
                    subject=subject,
                    semester=semester
                )

                if not created:
                    # If the enrollment already exists, add a validation message
                    duplicate_enrollments.append(f"{student.get_full_name()} is already enrolled in {subject.subject_name} for {semester.semester_name}.")
                else:
                    # If it's a retake, create a retake record
                    Retake.objects.create(subject_enrollment=subject_enrollment, reason="Retake due to failure or other reason")

        # Add success message
        if not duplicate_enrollments:
            messages.success(request, 'Students enrolled successfully!')
        else:
            # If there were duplicate enrollments, show an appropriate message
            messages.warning(request, 'Some students were already enrolled in the selected subjects.')

        return redirect('subjectEnrollmentList')

# Enrollled Student
@login_required
@permission_required('course.add_subjectenrollment', raise_exception=True)
def enrollStudent(request):
    student_role = Role.objects.get(name__iexact='student')
    profiles = Profile.objects.filter(role=student_role)
    subjects = Subject.objects.all()
    semesters = Semester.objects.all()

    # Group students by course
    students_by_course = {}
    for profile in profiles:
        course = profile.course or "No Course"
        if course not in students_by_course:
            students_by_course[course] = []
        students_by_course[course].append({
            'id': profile.id,
            'first_name': profile.first_name,
            'last_name': profile.last_name,
            'grade_year_level': profile.grade_year_level
        })

    year_levels = profiles.values_list('grade_year_level', flat=True).distinct().exclude(grade_year_level__isnull=True)
    return render(request, 'course/subjectEnrollment/enrollStudent.html', {
        'profiles': profiles,
        'subjects': subjects,
        'semesters': semesters,
        'students_by_course': students_by_course,  # Pass the grouped data
        'year_levels': year_levels,
    })


#enrolled Student List
@login_required
@permission_required('course.view_subjectenrollment', raise_exception=True)
def subjectEnrollmentList(request):
    user = request.user
    selected_semester_id = request.GET.get('semester', None)  # Get the selected semester from the query parameters
    selected_subject_id = request.GET.get('subject', None)  # Get the selected subject from the query parameters

    def get_current_semester():
        today = date.today()
        return Semester.objects.filter(start_date__lte=today, end_date__gte=today).first()

    current_semester = get_current_semester()

    if selected_semester_id:
        selected_semester = get_object_or_404(Semester, id=selected_semester_id)
    else:
        # If no semester is selected and there's no active semester, show all terms
        selected_semester = current_semester if current_semester else None

    if user.profile.role.name.lower() == 'teacher':
        enrollments = SubjectEnrollment.objects.select_related('subject', 'semester', 'student').filter(subject__assign_teacher=user)
    else:
        enrollments = SubjectEnrollment.objects.select_related('subject', 'semester', 'student')

    if selected_semester:
        enrollments = enrollments.filter(semester=selected_semester)

    if selected_subject_id:
        selected_subject = get_object_or_404(Subject, id=selected_subject_id)
        enrollments = enrollments.filter(subject=selected_subject)
    else:
        selected_subject = None

    subjects = {}
    for enrollment in enrollments:
        if enrollment.subject not in subjects:
            subjects[enrollment.subject] = []
        subjects[enrollment.subject].append(enrollment)

    semesters = Semester.objects.all()  # Get all semesters for the dropdown
    available_subjects = Subject.objects.filter(subjectenrollment__semester=selected_semester).distinct() if selected_semester else Subject.objects.all()

    return render(request, 'course/subjectEnrollment/enrolledStudentList.html', {
        'subjects': subjects,
        'semesters': semesters,
        'selected_semester': selected_semester,
        'available_subjects': available_subjects,
        'selected_subject': selected_subject,
        'current_semester': current_semester,
    })

@login_required
@permission_required('course.delete_subjectenrollment', raise_exception=True)
def dropStudentFromSubject(request, enrollment_id):
    enrollment = get_object_or_404(SubjectEnrollment, id=enrollment_id)
    enrollment.delete()
    messages.success(request, f"{enrollment.student.get_full_name()} has been dropped from {enrollment.subject.subject_name}.")
    return redirect('subjectEnrollmentList')


# Display the module based on the subject
@login_required
def subjectDetail(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    user = request.user

    assignment_activity_type = ActivityType.objects.filter(name="Assignment").first()
    quiz_activity_type = ActivityType.objects.filter(name="Quiz").first()
    exam_activity_type = ActivityType.objects.filter(name="Exam").first()
    participation_activity_type = ActivityType.objects.filter(name="Participation").first()

    # Ensure that IDs are assigned only when activity types are found
    assignment_activity_type_id = assignment_activity_type.id if assignment_activity_type else None
    quiz_activity_type_id = quiz_activity_type.id if quiz_activity_type else None
    exam_activity_type_id = exam_activity_type.id if exam_activity_type else None
    participation_activity_type_id = participation_activity_type.id if participation_activity_type else None

    selected_semester_id = request.GET.get('semester')
    selected_semester = None

    if selected_semester_id and selected_semester_id != 'None':
        selected_semester = get_object_or_404(Semester, id=selected_semester_id)
        terms = Term.objects.filter(semester=selected_semester)
    else:
        now = timezone.localtime(timezone.now())
        selected_semester = Semester.objects.filter(start_date__lte=now, end_date__gte=now).first()
        terms = Term.objects.filter(semester=selected_semester)

    is_student = user.is_authenticated and user.profile.role.name.lower() == 'student'
    is_teacher = user.is_authenticated and user.profile.role.name.lower() == 'teacher'
    
    answered_activity_ids = []
    
    if is_student:
        completed_activities = StudentQuestion.objects.filter(
            student=user, 
            activity_question__activity__term__in=terms,  # Filter by terms within the selected semester
            score__gt=0
        ).values_list('activity_question__activity_id', flat=True).distinct()
        
        answered_essays = StudentQuestion.objects.filter(
            student=user,
            activity_question__quiz_type__name='Essay',
            activity_question__activity__term__in=terms,  # Filter by terms within the selected semester
            student_answer__isnull=False
        ).values_list('activity_question__activity_id', flat=True).distinct()
        
        answered_documents = StudentQuestion.objects.filter(
            student=user,
            activity_question__quiz_type__name='Document',
            activity_question__activity__term__in=terms,  # Filter by terms within the selected semester
            uploaded_file__isnull=False,
            status=True
        ).values_list('activity_question__activity_id', flat=True).distinct()

        answered_activity_ids = set(completed_activities).union(answered_essays, answered_documents)
        
        activities = Activity.objects.filter(
            Q(subject=subject) & Q(term__in=terms) & 
            (Q(remedial=False) | Q(remedial=True, studentactivity__student=user))
        ).distinct()
        
        finished_activities = activities.filter(
            end_time__lte=timezone.localtime(timezone.now()), 
            id__in=answered_activity_ids
        )
        ongoing_activities = activities.filter(
            start_time__lte=timezone.localtime(timezone.now()), 
            end_time__gte=timezone.localtime(timezone.now())
        ).exclude(
            id__in=StudentQuestion.objects.filter(
                is_participation=True
            ).values_list('activity_id', flat=True)
        )
        upcoming_activities = activities.filter(start_time__gt=timezone.localtime(timezone.now())).exclude(
            id__in=StudentQuestion.objects.filter(
                is_participation=True
            ).values_list('activity_id', flat=True)  
        )

        # Adjusted module visibility logic
        modules = Module.objects.filter(subject=subject, term__semester=selected_semester).exclude(
            Q(term__isnull=True) | Q(start_date__isnull=True) | Q(end_date__isnull=True)
            ).order_by('order')
        visible_modules = []

        for module in modules:
            if not module.display_lesson_for_selected_users.exists() or user in module.display_lesson_for_selected_users.all():
                visible_modules.append(module)
    else:
        modules = Module.objects.filter( Q(term__semester=selected_semester) |
        Q(term__isnull=True, start_date__isnull=True, end_date__isnull=True),
        subject=subject).order_by('order')

        activities = Activity.objects.filter(subject=subject, term__in=terms)

        finished_activities = activities.filter(
            end_time__lte=timezone.localtime(timezone.now())
        )
        ongoing_activities = activities.filter(
            start_time__lte=timezone.localtime(timezone.now()), 
            end_time__gte=timezone.localtime(timezone.now())
        ).exclude(
            id__in=StudentQuestion.objects.filter(
                is_participation=True
            ).values_list('activity_id', flat=True)  # Exclude participation activities
        )
        upcoming_activities = activities.filter(start_time__gt=timezone.localtime(timezone.now())).exclude(
            id__in=StudentQuestion.objects.filter(
                is_participation=True
            ).values_list('activity_id', flat=True)  # Exclude participation activities
        )

    activities_with_grading_needed = []
    ungraded_items_count = 0
    if is_teacher:
        for activity in activities:
            questions_requiring_grading = ActivityQuestion.objects.filter(
                activity=activity,
                quiz_type__name__in=['Essay', 'Document']
            )
            ungraded_items = StudentQuestion.objects.filter(
                Q(activity_question__in=questions_requiring_grading),
                Q(student_answer__isnull=False) | Q(uploaded_file__isnull=False),
                status=True, 
                score=0  
            )
            if ungraded_items.exists():
                activities_with_grading_needed.append((activity, ungraded_items.count()))
                ungraded_items_count += ungraded_items.count()

    activities_by_module = defaultdict(list)
    for activity in activities:
        if activity.module:
            activities_by_module[activity.module.id].append(activity)

    # Attach activities to each module directly in the context
    for module in modules:
        module.activities = activities_by_module[module.id]
        module.red_flag = not module.term or not module.start_date or not module.end_date

    form = moduleForm()

    return render(request, 'course/viewSubjectModule.html', {
        'subject': subject,
        'modules': modules,
        'ongoing_activities': ongoing_activities,
        'upcoming_activities': upcoming_activities,
        'finished_activities': finished_activities,
        'activities_with_grading_needed': activities_with_grading_needed,
        'is_student': is_student,
        'is_teacher': is_teacher,
        'ungraded_items_count': ungraded_items_count,
        'selected_semester_id': selected_semester_id,
        'selected_semester': selected_semester,
        'answered_activity_ids': answered_activity_ids,
        'form': form,
        'assignment_activity_type_id': assignment_activity_type_id,
        'quiz_activity_type_id': quiz_activity_type_id, 
        'exam_activity_type_id': exam_activity_type_id,
        'participation_activity_type_id': participation_activity_type_id,
    })

@login_required
def termActivitiesGraph(request, subject_id):
    now = timezone.now()
    current_semester = Semester.objects.filter(start_date__lte=now, end_date__gte=now).first()
    if not current_semester:
        return JsonResponse({"error": "No active semester found."}, status=404)

    # Get the subject based on the provided subject_id
    subject = Subject.objects.filter(id=subject_id).first()
    if not subject:
        return JsonResponse({"error": "Subject not found."}, status=404)

    terms = Term.objects.filter(semester=current_semester)

    user = request.user
    is_student = user.is_authenticated and user.profile.role.name.lower() == 'student'
    is_teacher = user.is_authenticated and user.profile.role.name.lower() == 'teacher'

    activity_data = {}
    term_colors = ['rgba(75, 192, 192, 0.2)', 'rgba(54, 162, 235, 0.2)', 'rgba(255, 206, 86, 0.2)', 'rgba(153, 102, 255, 0.2)']
    border_colors = ['rgba(75, 192, 192, 1)', 'rgba(54, 162, 235, 1)', 'rgba(255, 206, 86, 1)', 'rgba(153, 102, 255, 1)']

    for i, term in enumerate(terms):
        # Filter activities by term and subject
        activities = Activity.objects.filter(term=term, subject=subject, end_time__lt=now).exclude(activity_type__name='Participation')

        # Initialize term data for combined completed and missed counts for each activity_type
        if term.term_name not in activity_data:
            activity_data[term.term_name] = {
                'id': term.id,
                'activity_types': {},  # Store activity_type specific data here
                'term_color': term_colors[i % len(term_colors)],  # Cycle through term colors
                'term_border_color': border_colors[i % len(border_colors)]
            }

        # Loop through activities and sum completed/missed students for each activity_type
        for activity in activities:
            activity_type_name = activity.activity_type.name  # Get the activity type (e.g., 'Quiz', 'Assignment')

            # Initialize the activity type data if not already present
            if activity_type_name not in activity_data[term.term_name]['activity_types']:
                activity_data[term.term_name]['activity_types'][activity_type_name] = {
                    'completed': 0,  # Sum of all completed activities for this activity_type
                    'missed': 0,     # Sum of all missed activities for this activity_type
                }

            if is_teacher:
                total_students = CustomUser.objects.filter(subjectenrollment__subject=activity.subject).distinct().count()
                completed_students = StudentQuestion.objects.filter(activity_question__activity=activity, status=True).values('student').distinct().count()
                missed_students = total_students - completed_students

                # Add completed and missed counts to the activity_type's total
                activity_data[term.term_name]['activity_types'][activity_type_name]['completed'] += completed_students
                activity_data[term.term_name]['activity_types'][activity_type_name]['missed'] += -missed_students

            elif is_student:
                completed_student = StudentQuestion.objects.filter(
                    student=user,  # Filter by logged-in student
                    activity_question__activity=activity,
                    status=True
                ).exists()

                # Increment completed or missed count for the student
                if completed_student:
                    activity_data[term.term_name]['activity_types'][activity_type_name]['completed'] += 1
                else:
                    activity_data[term.term_name]['activity_types'][activity_type_name]['missed'] += -1

    # Prepare the JSON response data, summing per term and per activity type
    response_data = {
        'semester': current_semester.semester_name,
        'subject': subject.subject_name,  # Include subject information
        'terms': activity_data  # Aggregated data by term and activity type
    }

    return JsonResponse(response_data)

@login_required
def displayActivitiesForTerm(request, subject_id, term_id, activity_type, activity_name):
    now = timezone.localtime(timezone.now())
    
    # Get the current semester
    current_semester = Semester.objects.filter(start_date__lte=now, end_date__gte=now).first()
    if not current_semester:
        return JsonResponse({"error": "No active semester found."}, status=404)

    term = get_object_or_404(Term, id=term_id, semester=current_semester)
    subject = get_object_or_404(Subject, id=subject_id)

    # Filter activities based on the term, subject, and activity type (e.g., Quiz, Assignment)
    if activity_type == 'completed':
        activities = Activity.objects.filter(term=term, subject=subject, end_time__lt=now, activity_type__name=activity_name)
    elif activity_type == 'missed':
        # Assuming missed activities are those that were not completed (add your custom logic here)
        activities = Activity.objects.filter(term=term, subject=subject, end_time__lt=now, activity_type__name=activity_name)

    return render(request, 'course/activitiesPerTerm.html', {
        'activities': activities,
        'term': term,
        'subject': subject,
        'activity_type': activity_type,
        'activity_name': activity_name,
    })


# get all the finished activities
@login_required
def subjectFinishedActivities(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    user = request.user
    
    is_student = user.is_authenticated and user.profile.role.name.lower() == 'student'
    is_teacher = user.is_authenticated and user.profile.role.name.lower() == 'teacher'
    
    now = timezone.localtime(timezone.now())
    
    # Get the semester associated with the subject via the SubjectEnrollment model
    subject_enrollment = SubjectEnrollment.objects.filter(subject=subject).first()
    if subject_enrollment:
        semester = subject_enrollment.semester
        semester_ended = semester.end_date < now.date()  # Compare only the date part
    else:
        semester_ended = False
    
    if is_student:
        student_activities = StudentQuestion.objects.filter(
            student=user
        ).values_list('activity_question__activity_id', flat=True).distinct()

        finished_activities = Activity.objects.filter(
            subject=subject,
            end_time__lt=now,  # Ensure the activity has ended
            id__in=student_activities
        )
    else:
        finished_activities = Activity.objects.filter(
            subject=subject,
            end_time__lt=now,  # Ensure the activity has ended
            id__in=StudentQuestion.objects.values_list('activity_question__activity_id', flat=True).distinct()
        )

    return render(request, 'course/subjectFinishedActivity.html', {
        'subject': subject,
        'finished_activities': finished_activities,
        'is_student': is_student,
        'is_teacher': is_teacher,
        'semester_ended': semester_ended,  # Pass the variable to the template
    })



# Display the student list for a subject
@login_required
def subjectStudentList(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    
    selected_semester_id = request.GET.get('semester')
    selected_semester = None

    if selected_semester_id and selected_semester_id.strip() and selected_semester_id != 'None':
        try:
            selected_semester = Semester.objects.get(id=selected_semester_id)
        except Semester.DoesNotExist:
            selected_semester = None

    if not selected_semester:
        now = timezone.localtime(timezone.now())
        selected_semester = Semester.objects.filter(start_date__lte=now, end_date__gte=now).first()

    if not selected_semester:
        return HttpResponse("No active semester found.", status=404)

    students = CustomUser.objects.filter(
        subjectenrollment__subject=subject,
        subjectenrollment__semester=selected_semester
    ).distinct()

    return render(request, 'course/viewStudentRoster.html', {
        'subject': subject,
        'students': students,
        'selected_semester': selected_semester,
    })


# display subject based on semester
@login_required
def subjectList(request):
    user = request.user
    profile = get_object_or_404(Profile, user=user)

    semesters = Semester.objects.all()

    current_date = timezone.localtime(timezone.now()).date()
    current_semester = Semester.objects.filter(start_date__lte=current_date, end_date__gte=current_date).first()

    selected_semester_id = request.GET.get('semester', None)

    if selected_semester_id:
        selected_semester = get_object_or_404(Semester, id=selected_semester_id)
    else:
        selected_semester = current_semester

    # Handle subject filtering based on roles
    if profile.role.name.lower() == 'student':
        subjects = Subject.objects.filter(
            subjectenrollment__student=user,
            subjectenrollment__semester=selected_semester
        ).distinct()
    elif profile.role.name.lower() == 'teacher':
        subjects = Subject.objects.filter(
            assign_teacher=user,
            subjectenrollment__semester=selected_semester
        ).distinct()
    else:
        # For admin, registrar, or other roles, display all subjects for the selected semester
        subjects = Subject.objects.filter(
            subjectenrollment__semester=selected_semester
        ).distinct()

    if not selected_semester:
        subjects = Subject.objects.none()

    for subject in subjects:
        # Get all modules for the subject
        modules = Module.objects.filter(subject=subject)
        total_modules = modules.count()

        if total_modules > 0:
            # Get average progress of the student for all modules in this subject
            avg_progress = StudentProgress.objects.filter(
                student=user,
                module__in=modules
            ).aggregate(average_progress=Avg('progress'))['average_progress'] or 0

            # Attach the calculated progress to the subject object
            subject.student_progress = avg_progress
        else:
            subject.student_progress = 0

    return render(request, 'course/subjectList.html', {
        'subjects': subjects,
        'semesters': semesters,
        'selected_semester_id': selected_semester_id,
        'selected_semester': selected_semester, 
        'current_semester': current_semester,
    })

# Display semester list
@login_required
@permission_required('course.view_semester', raise_exception=True)
def semesterList(request):
    semesters = Semester.objects.all().order_by('-create_at')
    form = semesterForm()
    return render(request, 'course/semester/semesterList.html', {
        'semesters': semesters, 'form': form,
    })


# Create Semester
@login_required
@permission_required('course.add_semester', raise_exception=True)
def createSemester(request):
    # Fetch all unavailable date ranges (start and end dates) for frontend validation
    unavailable_dates = Semester.objects.values_list('start_date', 'end_date')
    unavailable_dates_formatted = [
        (DateFormat(start).format('Y-m-d'), DateFormat(end).format('Y-m-d')) 
        for start, end in unavailable_dates
    ]

    errors = []  # Initialize an empty list to store error messages

    if request.method == 'POST':
        form = semesterForm(request.POST)

        # Extract start_date and end_date directly from POST data
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        school_year = request.POST.get('school_year')

        # Check if start_date or end_date is missing
        if not start_date or not end_date:
            errors.append("Both start and end dates are required.")
        else:
            # Convert the date strings to proper date objects for comparison
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                errors.append("Invalid date format. Please enter dates in 'YYYY-MM-DD' format.")

            if start_date and end_date:
                # Check if the start date is after or equal to the end date
                if start_date >= end_date:
                    errors.append("End date must be after the start date.")

                start_year = start_date.year
                end_year = end_date.year

                if int(school_year) != start_year or int(school_year) != end_year:
                    errors.append(f"The selected year {school_year} must match the start and end dates year.")

                # Check for overlapping semesters within the same school year
                overlapping_semesters = Semester.objects.filter(
                    school_year=school_year
                ).filter(
                    # Check if the new semester's start date falls within an existing semester
                    start_date__lte=end_date,  # The existing semester starts before or on the new semester's end date
                    end_date__gte=start_date   # The existing semester ends after or on the new semester's start date
                )

                if overlapping_semesters.exists():
                    errors.append("The selected dates overlap with an existing semester.")

        # If no custom validation errors, proceed with form validation
        if not errors and form.is_valid():
            form.save()
            messages.success(request, 'Semester created successfully!')
            return redirect('semesterList')
        else:
            if errors:
                for error in errors:
                    messages.error(request, error)
            else:
                messages.error(request, 'There was an error creating the semester. Please try again.')

            return redirect('semesterList')  # Single redirect after all error handling

    else:
        form = semesterForm()

    return render(request, 'course/semester/createSemester.html', {
        'form': form,
        'disabled_dates': unavailable_dates_formatted  # Pass the formatted unavailable dates to the template for JS
    })


# Update Semester
@login_required
@permission_required('course.change_semester', raise_exception=True)
def updateSemester(request, pk):
    semester = get_object_or_404(Semester, pk=pk)

    # Fetch all unavailable date ranges (excluding the current semester being updated)
    unavailable_dates = Semester.objects.exclude(pk=pk).values_list('start_date', 'end_date')
    unavailable_dates_formatted = [
        (DateFormat(start).format('Y-m-d'), DateFormat(end).format('Y-m-d')) 
        for start, end in unavailable_dates
    ]

    errors = []  # Initialize an empty list to store custom error messages

    if request.method == 'POST':
        form = semesterForm(request.POST, instance=semester)

        # Extract start_date and end_date directly from POST data
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        school_year = request.POST.get('school_year')

        # Check if start_date or end_date is missing
        if not start_date or not end_date:
            errors.append("Both start and end dates are required.")
        else:
            # Convert the date strings to proper date objects for comparison
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                errors.append("Invalid date format. Please enter dates in 'YYYY-MM-DD' format.")

            if start_date and end_date:
                # Check if the start date is after or equal to the end date
                if start_date >= end_date:
                    errors.append("End date must be after the start date.")

                start_year = start_date.year
                end_year = end_date.year

                if int(school_year) != start_year or int(school_year) != end_year:
                    errors.append(f"The selected year {school_year} must match the start and end dates year.")

                # Check for overlapping semesters within the same school year
                overlapping_semesters = Semester.objects.filter(
                    school_year=school_year
                    ).filter(
                    Q(start_date__lte=end_date, end_date__gte=start_date) |
                    Q(start_date__gte=start_date, end_date__lte=end_date)  # The existing semester ends after or on the new semester's start date
                ).exclude(pk=semester.pk)  # Exclude the current semester from the overlap check

                if overlapping_semesters.exists():
                    errors.append("The selected dates overlap with an existing semester.")

        # If no custom validation errors, proceed with form validation
        if not errors and form.is_valid():
            form.save()
            messages.success(request, 'Semester updated successfully!')
            return redirect('semesterList')
        else:
            # Add custom errors to the Django messages framework
            if errors:
                for error in errors:
                    messages.error(request, error)
            else:
                messages.error(request, 'There was an error updating the semester. Please try again.')
            
            return redirect('semesterList')

    else:
        form = semesterForm(instance=semester)

    return render(request, 'course/semester/updateSemester.html', {
        'form': form,
        'semester': semester,
        'disabled_dates': unavailable_dates_formatted  # Pass the formatted unavailable dates to the template for JS
    })

@login_required
@permission_required('course.delete_semester', raise_exception=True)
def delete_semester(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    try:
        semester.delete()
        messages.success(request, 'Semester deleted successfully!')
    except ProtectedError as e:
        messages.error(request, f"Cannot delete this semester because it is referenced by other records.")

    return redirect('semesterList')

@login_required
def endSemester(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    semester.end_semester = True
    semester.save()
    messages.success(request, 'Semester ended successfully!')
    return redirect('semesterList')


@login_required
def previousSemestersView(request):
    user = request.user
    profile = get_object_or_404(Profile, user=user)

    # Get only finished semesters
    current_date = timezone.localtime(timezone.now()).date()
    finished_semesters = Semester.objects.filter(end_date__lt=current_date).order_by('-end_date')

    selected_semester_id = request.GET.get('semester', None)

    if selected_semester_id:
        selected_semester = get_object_or_404(Semester, id=selected_semester_id)
    else:
        selected_semester = finished_semesters.first() 

    if profile.role.name.lower() == 'student':
        subjects = Subject.objects.filter(
            subjectenrollment__student=user,
            subjectenrollment__semester=selected_semester
        ).distinct()
    elif profile.role.name.lower() == 'teacher':
        subjects = Subject.objects.filter(
            assign_teacher=user,
            subjectenrollment__semester=selected_semester
        ).distinct()
    else:
        subjects = Subject.objects.filter(
            subjectenrollment__semester=selected_semester
        ).distinct()

    if not selected_semester:
        subjects = Subject.objects.none()

    return render(request, 'course/archivedSemester.html', {
        'subjects': subjects,
        'semesters': finished_semesters,  # Only show finished semesters
        'selected_semester_id': selected_semester_id,
        'selected_semester': selected_semester,
    })

# Display term list
@login_required
@permission_required('course.view_term', raise_exception=True)
def termList(request):
    current_date = timezone.now().date()
    current_semester = Semester.objects.filter(start_date__lte=current_date, end_date__gte=current_date).first()

    view_all_terms = request.GET.get('view_all_terms')

    if view_all_terms:
        terms = Term.objects.all()

    else:
        terms = Term.objects.filter(semester=current_semester) 

    form = termForm()
    return render(request, 'course/term/termList.html', {
        'terms': terms,
        'form': form,
        'view_all_terms': view_all_terms,
    })

# Create Semester
@login_required
@permission_required('course.add_term', raise_exception=True)
def createTerm(request):
    if request.method == 'POST':
        form = termForm(request.POST)

        semester = request.POST.get('semester')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        errors = []

        # Check if start_date or end_date is missing
        if not start_date or not end_date:
            errors.append("Both start and end dates are required.")
        else:
            # Convert the date strings to proper date objects for comparison
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                errors.append("Invalid date format. Please enter dates in 'YYYY-MM-DD' format.")

            if start_date and end_date:
                # Check if the start date is after or equal to the end date
                if start_date >= end_date:
                    errors.append("End date must be after the start date.")

                # Check for overlapping semesters within the same school year
                overlapping_semesters = Term.objects.filter(
                    semester= semester,
                    start_date__lt=end_date,  # Existing semester starts before the new semester ends
                    end_date__gt=start_date   # Existing semester ends after the new semester starts
                )

                if overlapping_semesters.exists():
                    errors.append("The selected dates overlap with an existing term.")
                    
        if not errors and form.is_valid():
            term = form.save(commit=False)
            term.created_by = request.user  
            term.save()
            messages.success(request, 'Term created successfully!')
            return redirect('termList')
        else:
            if errors:
                for error in errors:
                    messages.error(request, error)
            else:
                messages.error(request, 'There was an error creating the term. Please try again.')
            return redirect('termList')
            
    else:
        form = termForm()
    return render(request, 'course/term/createTerm.html', {
        'form': form,
    })

# Update Semester
@login_required
@permission_required('course.change_term', raise_exception=True)
def updateTerm(request, pk):
    term = get_object_or_404(Term, pk=pk)

    if request.method == 'POST':
        form = termForm(request.POST, instance=term)

        semester = request.POST.get('semester')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        errors = []

        # Check if start_date or end_date is missing
        if not start_date or not end_date:
            errors.append("Both start and end dates are required.")
        else:
            # Convert the date strings to proper date objects for comparison
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                errors.append("Invalid date format. Please enter dates in 'YYYY-MM-DD' format.")

            if start_date and end_date:
                # Check if the start date is after or equal to the end date
                if start_date >= end_date:
                    errors.append("End date must be after the start date.")

                # Check for overlapping semesters within the same school year
                overlapping_semesters = Term.objects.filter(
                    semester= semester,
                    start_date__lt=end_date,  # Existing semester starts before the new semester ends
                    end_date__gt=start_date   # Existing semester ends after the new semester starts
                ).exclude(pk=term.pk)  # Exclude the current semester from the overlap check

                if overlapping_semesters.exists():
                    errors.append("The selected dates overlap with an existing term.")

        if not errors and form.is_valid():
            form.save()
            messages.success(request, 'Term updated successfully!')
            return redirect('termList')
        else:
            if errors:
                for error in errors:
                    messages.error(request, error)
            else:
                messages.error(request, 'There was an error creating the term. Please try again.')
            return redirect('termList')
    else:
        form = termForm(instance=term)
        
    return render(request, 'course/term/updateTerm.html', {
        'form': form, 
        'term': term
    })

@login_required
def deleteTerm(request, pk):
    term = get_object_or_404(Term, pk=pk)
    term.delete()
    messages.success(request, 'Term deleted successfully!')
    return redirect('termList')

# Participation Scores
@login_required
def selectParticipation(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)

    if request.method == 'POST':
        form = ParticipationForm(request.POST, initial={'subject': subject})
        if form.is_valid():
            term = form.cleaned_data['term']
            max_score = form.cleaned_data['max_score']
            return redirect('participationScore', subject_id=subject.id, term_id=term.id, max_score=int(max_score))
    else:
        form = ParticipationForm(initial={'subject': subject})
        form.fields['subject'].widget = forms.HiddenInput()

    return render(request, 'course/participation/selectParticipation.html', {'form': form})



class CopyActivitiesView(View):
    def get(self, request, subject_id):
        subject = get_object_or_404(Subject, id=subject_id)
        semesters = Semester.objects.all()
        return render(request, 'course/copyActivities.html', {
            'subject': subject,
            'semesters': semesters,
        })

    def post(self, request, subject_id):
        try:
            subject = get_object_or_404(Subject, id=subject_id)
            from_semester_id = request.POST.get('from_semester')
            to_semester_id = request.POST.get('to_semester')


            if from_semester_id and to_semester_id:

                if from_semester_id == to_semester_id:
                    messages.error(request, "You cannot copy activities to the same semester.")
                    return redirect('subjectDetail', pk=subject_id)
                
                result = copy_activities_from_previous_semester(subject_id, from_semester_id, to_semester_id)
                messages.success(request, result)
            else:
                messages.error(request, "Please select both the semesters.")

            return redirect('subjectDetail', pk=subject_id)

        except Exception as e:
            print(f"Error: {e}")
            messages.error(request, "An error occurred while processing your request. : {e}")
            return redirect('subjectDetail', pk=subject_id)
        

@csrf_exempt
def create_teams_meeting_view(request, subject_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            subject = data.get('subject')
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            organizer_email = data.get('organizer_email')

            # Log the data for debugging
            print(f"Subject: {subject}, Start time: {start_time}, End time: {end_time}, Organizer email: {organizer_email}")

            if not subject or not start_time or not end_time or not organizer_email:
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            # Call the function to create the Teams meeting
            meeting_data = create_teams_meeting(organizer_email, subject, start_time, end_time)

            # If meeting creation was successful, return the meeting URL
            if 'joinUrl' in meeting_data:
                return JsonResponse({'meetingUrl': meeting_data['joinUrl']})
            return JsonResponse({'error': 'Unable to create meeting'}, status=400)
        
        except Exception as e:
            print(f"Error creating meeting: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    return HttpResponseBadRequest("Invalid request method.")