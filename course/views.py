from django.shortcuts import render, redirect, get_object_or_404
from .models import SubjectEnrollment, Semester, Term, Retake
from accounts.models import Profile
from subject.models import Subject
from roles.models import Role
from module.models import Module
from activity.models import Activity ,StudentQuestion, ActivityQuestion
from django.views import View
import json
from django.core.serializers.json import DjangoJSONEncoder
from accounts.models import CustomUser
from django.utils import timezone
from .forms import semesterForm, termForm, ParticipationForm
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
from collections import defaultdict
from django.http import JsonResponse

# Handle the enrollment of students
@method_decorator(login_required, name='dispatch')
class enrollStudentView(View):
    def post(self, request, *args, **kwargs):
        student_profile_id = request.POST.get('student_profile')
        subject_ids = request.POST.getlist('subject_ids')
        semester_id = request.POST.get('semester_id')

        student_profile = get_object_or_404(Profile, id=student_profile_id)
        student = student_profile.user
        subjects = Subject.objects.filter(id__in=subject_ids)
        semester = get_object_or_404(Semester, id=semester_id)

        for subject in subjects:
            subject_enrollment, created = SubjectEnrollment.objects.get_or_create(
                student=student,
                subject=subject,
                semester=semester
            )

            if not created:
                Retake.objects.create(subject_enrollment=subject_enrollment, reason="Retake due to failure or other reason")

        return redirect('subjectEnrollmentList')

# Enrollled Student
@login_required
@permission_required('course.add_subjectenrollment', raise_exception=True)
def enrollStudent(request):
    student_role = Role.objects.get(name__iexact='student')
    profiles = Profile.objects.filter(role=student_role)
    subjects = Subject.objects.all()
    semesters = Semester.objects.all()

    profiles_json = json.dumps(list(profiles.values('id', 'first_name', 'last_name', 'student_status')), cls=DjangoJSONEncoder)
    
    return render(request, 'course/subjectEnrollment/enrollStudent.html', {
        'profiles': profiles,
        'profiles_json': profiles_json,
        'subjects': subjects,
        'semesters': semesters
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
        modules = Module.objects.filter(subject=subject, term__semester=selected_semester).order_by('order')
        print(f"Modules found: {modules.count()}")
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
        activities = Activity.objects.filter(term=term, subject=subject, end_time__lt=now)

        # Initialize term data for combined completed and missed counts
        if term.term_name not in activity_data:
            activity_data[term.term_name] = {
                'id': term.id, 
                'completed': 0,  # Sum of all completed activities in this term
                'missed': 0,     # Sum of all missed activities in this term
                'term_color': term_colors[i % len(term_colors)],  # Cycle through term colors
                'term_border_color': border_colors[i % len(border_colors)]
            }

        # Loop through activities and sum completed/missed students
        if is_teacher:
            for activity in activities:
                total_students = CustomUser.objects.filter(subjectenrollment__subject=activity.subject).distinct().count()
                completed_students = StudentQuestion.objects.filter(activity_question__activity=activity, status=True).values('student').distinct().count()
                missed_students = total_students - completed_students

                # Add completed and missed counts to the term's total
                activity_data[term.term_name]['completed'] += completed_students
                activity_data[term.term_name]['missed'] += -missed_students  # Missed students stored as negative

        elif is_student:
            for activity in activities:
                completed_student = StudentQuestion.objects.filter(
                    student=user,  # Filter by logged-in student
                    activity_question__activity=activity,
                    status=True
                ).exists()

                # Increment completed or missed count for the student
                if completed_student:
                    activity_data[term.term_name]['completed'] += 1
                else:
                    activity_data[term.term_name]['missed'] += -1

    # Prepare the JSON response data, summing per term rather than per activity
    response_data = {
        'semester': current_semester.semester_name,
        'subject': subject.subject_name,  # Include subject information
        'terms': activity_data  # Aggregated data by term
    }

    return JsonResponse(response_data)


def displayActivitiesForTerm(request, subject_id, term_id, activity_type):
    now = timezone.localtime(timezone.now())
    
    # Get the current semester
    current_semester = Semester.objects.filter(start_date__lte=now, end_date__gte=now).first()
    if not current_semester:
        return JsonResponse({"error": "No active semester found."}, status=404)

    term = get_object_or_404(Term, id=term_id, semester=current_semester)
    subject = get_object_or_404(Subject, id=subject_id)

    # Filter activities based on the term, subject, and activity type (completed or missed)
    if activity_type == 'completed':
        activities = Activity.objects.filter(term=term, subject=subject, end_time__lt=now)
    elif activity_type == 'missed':
        activities = Activity.objects.filter(term=term, subject=subject, end_time__lt=now)

    return render(request, 'course/activitiesPerTerm.html', {
        'activities': activities,
        'term': term,
        'subject': subject,
        'activity_type': activity_type,
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
    semesters = Semester.objects.all()
    form = semesterForm()
    return render(request, 'course/semester/semesterList.html', {
        'semesters': semesters, 'form': form,
    })


# Create Semester
@login_required
@permission_required('course.add_semester', raise_exception=True)
def createSemester(request):
    if request.method == 'POST':
        form = semesterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Semester created successfully!')
            return redirect('semesterList')
        else:
            messages.error(request, 'There was an error creating the semester. Please try again.')
    else:
        form = semesterForm()
    return render(request, 'course/semester/createSemester.html', {
        'form': form,
    })

# Update Semester
@login_required
@permission_required('course.change_semester', raise_exception=True)
def updateSemester(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if request.method == 'POST':
        form = semesterForm(request.POST, instance=semester)
        if form.is_valid():
            form.save()
            messages.success(request, 'Semester updated successfully!')
            return redirect('semesterList')
        else:
            messages.error(request, 'There was an error updating the semester. Please try again.')
    else:
        form = semesterForm(instance=semester)
    return render(request, 'course/semester/updateSemester.html', {
        'form': form, 'semester': semester
    })

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
        if form.is_valid():
            term = form.save(commit=False)
            term.created_by = request.user  
            term.save()
            messages.success(request, 'Term created successfully!')
            return redirect('termList')
        else:
            messages.error(request, 'There was an error creating the term. Please try again.')
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

    if term.created_by != request.user:
        messages.error(request, 'You do not have permission to edit this term.')
        return redirect('termList')

    if request.method == 'POST':
        form = termForm(request.POST, instance=term)
        if form.is_valid():
            form.save()
            messages.success(request, 'Term updated successfully!')
            return redirect('termList')
        else:
            messages.error(request, 'There was an error updating the term. Please try again.')
    else:
        form = termForm(instance=term)
        
    return render(request, 'course/term/updateterm.html', {
        'form': form, 
        'term': term
    })

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
            print("POST request received")
            subject = get_object_or_404(Subject, id=subject_id)
            from_semester_id = request.POST.get('from_semester')
            to_semester_id = request.POST.get('to_semester')

            print(f"From semester: {from_semester_id}, To semester: {to_semester_id}")

            if from_semester_id and to_semester_id:
                result = copy_activities_from_previous_semester(subject_id, from_semester_id, to_semester_id)
                messages.success(request, result)
            else:
                messages.error(request, "Please select both the semesters.")

            return redirect('subjectDetail', pk=subject_id)

        except Exception as e:
            print(f"Error: {str(e)}")
            messages.error(request, "An error occurred while processing your request.")
            return redirect('subjectDetail', pk=subject_id)