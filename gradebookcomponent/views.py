from django.shortcuts import render, redirect, get_object_or_404
from .forms import GradeBookComponentsForm, CopyGradeBookForm, TermGradeBookComponentsForm, SubGradeBookForm
from .models import GradeBookComponents, TermGradeBookComponents, SubGradeBook
from activity.models import StudentQuestion, Activity, ActivityQuestion, ActivityType
from accounts.models import CustomUser
from django.db.models import Sum, Max
from django.utils import timezone
from course.models import Semester, Term, StudentParticipationScore, SubjectEnrollment
from subject.models import Subject
from decimal import Decimal
from django.http import JsonResponse
from collections import defaultdict
from django.contrib import messages
from django.contrib.auth.decorators import login_required

#View GradeBookComponents
@login_required
def viewGradeBookComponents(request):
    today = timezone.now().date()
    current_semester = Semester.objects.filter(start_date__lte=today, end_date__gte=today).first()
    
    if current_semester:
        if request.user.profile.role.name.lower() == 'teacher':
            gradebookcomponents = GradeBookComponents.objects.filter(
                teacher=request.user, 
                subject__subjectenrollment__semester=current_semester
            ).distinct()
        else:
            gradebookcomponents = GradeBookComponents.objects.filter(
                subject__subjectenrollment__semester=current_semester
            ).distinct()
    else:
        gradebookcomponents = GradeBookComponents.objects.none()  # No current semester found
    
    return render(request, 'gradebookcomponent/gradebook/gradeBook.html', {'gradebookcomponents': gradebookcomponents})


#Create GradeBookComponents
@login_required
def createGradeBookComponents(request):
    if request.method == 'POST':
        form = GradeBookComponentsForm(request.POST, user=request.user)
        if form.is_valid():
            gradebook_component = form.save(commit=False)
            gradebook_component.teacher = request.user
            gradebook_component.save()
            messages.success(request, 'Gradebook created successfully!')
            return redirect('viewGradeBookComponents')
        else:
            messages.success(request, 'An error occured while creating gradebook!')
    else:
        form = GradeBookComponentsForm(user=request.user)
    
    return render(request, 'gradebookcomponent/gradebook/createGradeBook.html', {'form': form})

#Copy GradeBookComponents
@login_required
def copyGradeBookComponents(request):
    if request.method == 'POST':
        form = CopyGradeBookForm(request.POST, user=request.user)
        if form.is_valid():
            source_subject = form.cleaned_data['copy_from_subject']
            target_subjects = form.cleaned_data['subject']
            
            for target_subject in target_subjects:
                components_to_copy = GradeBookComponents.objects.filter(subject=source_subject, teacher=request.user)
                for component in components_to_copy:
                    if not GradeBookComponents.objects.filter(
                        subject=target_subject,
                        teacher=request.user,
                        activity_type=component.activity_type,
                        category_name=component.category_name
                    ).exists():
                        GradeBookComponents.objects.create(
                            teacher=request.user,
                            subject=target_subject,
                            activity_type=component.activity_type,
                            category_name=component.category_name,
                            percentage=component.percentage,
                        )
            messages.success(request, 'Gradebook copied successfully!')
            return redirect('viewGradeBookComponents')
        else:
            messages.error(request, 'An error occurred while copying the gradebook!')    
    else:
        form = CopyGradeBookForm(user=request.user)
    
    return render(request, 'gradebookcomponent/gradebook/copyGradeBook.html', {'form': form})

#Modify GradeBookComponents
@login_required
def updateGradeBookComponents(request, pk):
    gradebookcomponent = get_object_or_404(GradeBookComponents, pk=pk)
    if request.method == 'POST':
        form = GradeBookComponentsForm(request.POST, instance=gradebookcomponent)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gradebook updated successfully!')
            return redirect('viewGradeBookComponents')
        else:
            messages.success(request, 'An error occured while creating gradebook!')
    else:
        form = GradeBookComponentsForm(instance=gradebookcomponent)
    
    return render(request, 'gradebookcomponent/gradebook/updateGradeBook.html', {'form': form, 'gradebookcomponent':gradebookcomponent})

#Delete GradeBookComponents
@login_required
def deleteGradeBookComponents(request, pk):
    gradebookcomponent = get_object_or_404(GradeBookComponents, pk=pk)
    gradebookcomponent.delete()
    messages.success(request, 'Gradebook deleted successfully!')
    return redirect('viewGradeBookComponents')

@login_required
def subGradebook(request):
    subgradebook = SubGradeBook.objects.all()
    return render(request, 'gradebookcomponent/subgradebook/subGradebook.html',{'subgradebook':subgradebook})


@login_required
def createSubGradeBook(request):
    if request.method == 'POST':
        sub_gradebook = SubGradeBookForm(request.POST, user=request.user)
        if sub_gradebook.is_valid():
            sub_gradebook.save()
            messages.success(request, 'Sub Gradebook created successfully!')
            return redirect('subGradebook')
        else:
            messages.error(request, 'An error occurred while creating the sub gradebook!')
    else:
        # Pass the user to the form for GET requests as well
        sub_gradebook = SubGradeBookForm(user=request.user)

    return render(request, 'gradebookcomponent/subgradebook/createSubGradeBook.html', {'sub_gradebook': sub_gradebook})

def updateSubGradebook(request, id):
    sub_gradebook = get_object_or_404(SubGradeBook, id=id)
    if request.method == 'POST':
        form = SubGradeBookForm(request.POST, instance=sub_gradebook)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sub Gradebook updated successfully!')
            return redirect('subGradebook')
        else:
            messages.error(request, 'An error occurred while updating the sub gradebook!')
    else:
        form = SubGradeBookForm(instance=sub_gradebook)
    return render(request, 'gradebookcomponent/subgradebook/updateSubGradeBook.html', {'form': form, 'sub_gradebook': sub_gradebook})

def deleteSubGradebook(request, id):
    sub_gradebook = get_object_or_404(SubGradeBook, id=id)
    sub_gradebook.delete()
    messages.success(request, 'Sub Gradebook deleted successfully!')
    return redirect('subGradebook')

#View TermGradeBook List
@login_required
def termBookList(request):
    if request.user.profile.role.name.lower() == 'teacher':
        termbook = TermGradeBookComponents.objects.filter(teacher=request.user)
    else:
        termbook = TermGradeBookComponents.objects.all()
    return render(request, 'gradebookcomponent/termbook/TermBook.html', {'termbook': termbook})

#create TermGradeBook
@login_required
def createTermGradeBookComponent(request):
    if request.method == 'POST':
        form = TermGradeBookComponentsForm(request.POST, user=request.user)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.teacher = request.user  
            instance.save() 
            
            form.save_m2m() 
            messages.success(request, 'Termbook created successfully!')
            return redirect('termBookList')
        else:
            messages.error(request, 'An error occurred while creating the termbook!')
    else:
        form = TermGradeBookComponentsForm(user=request.user)

    return render(request, 'gradebookcomponent/termbook/createTermBook.html', {'form': form})

#update TermBook
@login_required
def updateTermBookComponent(request, id):
    termbook = get_object_or_404(TermGradeBookComponents, id=id)
    if request.method == 'POST':
        form = TermGradeBookComponentsForm(request.POST, instance=termbook, user=request.user)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.teacher = request.user  
            instance.save()  
            form.save_m2m() 

            messages.success(request, 'Termbook updated successfully!')
            return redirect('termBookList')
        else:
            messages.error(request, 'An error occurred while updating the termbook!')
    else:
        form = TermGradeBookComponentsForm(instance=termbook, user=request.user)

    return render(request, 'gradebookcomponent/termbook/updateTermBook.html', {'form': form, 'termbook': termbook})

#view Termbook
@login_required
def viewTermBookComponent(request, id=None):
    semesters = Semester.objects.all() 
    selected_semester = request.GET.get('semester')  

    if selected_semester:
        terms = TermGradeBookComponents.objects.filter(term__semester_id=selected_semester)
    else:
        terms = TermGradeBookComponents.objects.all()

    context = {
        'semesters': semesters,
        'selected_semester': selected_semester,
        'terms': terms,
    }
    return render(request, 'gradebookcomponent/termbook/viewTermBook.html', context)

#delete TermBook
@login_required
def deleteTermBookComponent(request, id):
    termbook = get_object_or_404(TermGradeBookComponents, id=id)
    termbook.delete()
    messages.success(request, 'Termbook deleted successfully!')
    return redirect('termBookList')


#Teacher (see all student scores for an activity)
@login_required
def teacherActivityView(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    student_scores = StudentQuestion.objects.filter(activity_question__activity=activity).values('student').annotate(total_score=Sum('score'))

    student_scores_with_names = []
    max_score = ActivityQuestion.objects.filter(activity=activity).aggregate(total_score=Sum('score'))['total_score'] or 0
    for entry in student_scores:
        student = get_object_or_404(CustomUser, id=entry['student'])
        submission_date = StudentQuestion.objects.filter(activity_question__activity=activity, student=student).aggregate(last_submission=Max('submission_time'))['last_submission']
        student_scores_with_names.append({
            'student': student,
            'total_score': entry['total_score'],
            'max_score': max_score,
            'submission_date': submission_date
        })

    return render(request, 'gradebookcomponent/activityGrade/teacherGradedActivity.html', {
        'activity': activity,
        'student_scores': student_scores_with_names,
    })


#Student (see all scores for his activity)
@login_required
def studentActivityView(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    user = request.user

    # Query based on whether the user is a student or teacher
    if user.profile.role.name.lower() == 'student':
        student_scores = StudentQuestion.objects.filter(
            activity_question__activity=activity, student=user
        ).values('student').annotate(total_score=Sum('score'))
    else:  # Assume the user is a teacher
        student_scores = StudentQuestion.objects.filter(
            activity_question__activity=activity
        ).values('student').annotate(total_score=Sum('score'))

    detailed_scores = []

    for student_score in student_scores:
        student = get_object_or_404(CustomUser, id=student_score['student'])
        questions = StudentQuestion.objects.filter(student=student, activity_question__activity=activity)
        max_score = ActivityQuestion.objects.filter(activity=activity).aggregate(total_score=Sum('score'))['total_score'] or 0
        question_details = []
        latest_submission_time = None

        for i, question in enumerate(questions, start=1):
            if question.activity_question.quiz_type.name == 'Document' and question.uploaded_file:
                student_answer_display = f"<a href='{question.uploaded_file.url}' target='_blank'>Download Document</a>"
            else:
                student_answer_display = question.student_answer or "No answer provided"

            if activity.show_score:
                question_details.append({
                    'number': i,
                    'question_text': question.activity_question.question_text,
                    'correct_answer': question.activity_question.correct_answer,
                    'student_answer': student_answer_display,
                    'score': question.score,
                })
            else:
                question_details.append({
                    'number': i,
                    'question_text': question.activity_question.question_text,
                    'student_answer': 'Student answer hidden',
                    'score': 'Score hidden',
                    'correct_answer': 'Answer hidden',
                })

            if latest_submission_time is None or (question.submission_time and question.submission_time > latest_submission_time):
                latest_submission_time = question.submission_time

        detailed_scores.append({
            'student': student,
            'total_score': student_score['total_score'],
            'max_score': max_score,
            'questions': question_details,
            'submission_time': latest_submission_time,
        })

    return render(request, 'gradebookcomponent/activityGrade/studentGradedActivity.html', {
        'activity': activity,
        'detailed_scores': detailed_scores,
    })

# fitler for getting the current semester
@login_required
def get_current_semester(request):
    current_date = timezone.now().date()
    try:
        current_semester = Semester.objects.get(start_date__lte=current_date, end_date__gte=current_date)
        return current_semester
    except Semester.DoesNotExist:
        return None

#Teacher (Student breakdown score for all activity)
@login_required
def studentTotalScore(request, student_id, subject_id):
    selected_semester_id = request.GET.get('semester', None)
    selected_term_id = request.GET.get('term', 'all')  # Capture selected term

    if selected_semester_id == 'null':
        selected_semester_id = None

    if selected_semester_id:
        current_semester = get_object_or_404(Semester, id=selected_semester_id)
    else:
        current_semester = get_current_semester(request)
        if not current_semester:
            return render(request, 'gradebookcomponent/activityGrade/studentGrade.html', {
                'error': 'No current semester found.'
            })

    user = request.user

    # Fetch the student and subject based on IDs, filtering by the selected semester
    student = get_object_or_404(CustomUser, id=student_id)
    subject = get_object_or_404(Subject, id=subject_id, subjectenrollment__student=student, subjectenrollment__semester=current_semester)

    activity_types = ActivityType.objects.exclude(name__iexact="Participation")  # Exclude participation activities
    terms = Term.objects.filter(semester=current_semester)

    term_scores_data = []

    for term in terms:
        if selected_term_id != 'all' and str(term.id) != selected_term_id:
            continue
        
        student_scores_data = []
        term_has_data = False

        # Loop through all non-participation activities
        for activity_type in activity_types:
            activities = Activity.objects.filter(term=term, activity_type=activity_type, subject=subject)

            try:
                gradebook_component = GradeBookComponents.objects.get(
                    teacher=user if user.profile.role.name.lower() == 'teacher' else subject.assign_teacher,
                    subject=subject, 
                    activity_type=activity_type
                )
                activity_percentage = gradebook_component.percentage
            except GradeBookComponents.DoesNotExist:
                activity_percentage = Decimal(0)

            for activity in activities:
                student_total_score = Decimal(0)
                max_score_sum = Decimal(0)

                student_questions = StudentQuestion.objects.filter(
                    student=student,
                    activity_question__activity=activity,
                    status=True 
                )

                if not student_questions.exists():
                    max_score = activity.activityquestion_set.aggregate(total_max_score=Sum('score'))['total_max_score'] or Decimal(0)
                    student_scores_data.append({
                        'student': student.get_full_name(),
                        'activity_name': activity.activity_name,
                        'question_text': 'No submission',
                        'score': 0,
                        'max_score': max_score,
                        'percentage': 0,
                        'weighted_score': 0,
                        'missed': True,
                        'submission_time': None,
                    })
                    continue

                for student_question in student_questions:
                    question = student_question.activity_question.question_text
                    score = student_question.score
                    max_score = student_question.activity_question.score

                    student_total_score += Decimal(score)
                    max_score_sum += Decimal(max_score)

                    student_scores_data.append({
                        'student': student.get_full_name(),
                        'activity_name': activity.activity_name,
                        'question_text': question,
                        'score': score,
                        'max_score': max_score,
                        'percentage': (Decimal(score) / Decimal(max_score)) * 100 if max_score > 0 else 0,
                        'weighted_score': (Decimal(score) / Decimal(max_score)) * activity_percentage if max_score > 0 else 0,
                        'missed': False,
                        'submission_time': student_question.submission_time,
                    })

                term_has_data = True

        # Now we handle participation scores separately from other activities
        participation_student_questions = StudentQuestion.objects.filter(
            student=student,
            activity__term=term,
            activity__subject=subject,
            is_participation=True  # Flag for participation
        )

        participation_total_score = Decimal(0)
        participation_max_score_sum = Decimal(0)

        if participation_student_questions.exists():
            for student_question in participation_student_questions:
                score = Decimal(student_question.score)
                participation_total_score += score
                participation_max_score_sum += 100  # Assuming the max score for participation is 100

            participation_percentage = (participation_total_score / participation_max_score_sum) * 100 if participation_max_score_sum > 0 else 0
            weighted_score = participation_total_score / participation_max_score_sum  # Assuming full weight

            student_scores_data.append({
                'student': student.get_full_name(),
                'activity_name': 'Participation',  # Label for participation
                'question_text': 'Participation Activity',
                'score': participation_total_score,
                'max_score': participation_max_score_sum,
                'percentage': participation_percentage,
                'weighted_score': weighted_score,
                'missed': participation_total_score == 0,
                'submission_time': None
            })

        if term_has_data or participation_student_questions.exists():
            term_scores_data.append({
                'term': term,
                'subject': subject,
                'student_scores_data': student_scores_data,
            })

    return render(request, 'gradebookcomponent/activityGrade/studentGrade.html', {
        'current_semester': current_semester,
        'terms': terms,
        'subjects': [subject],
        'term_scores_data': term_scores_data,
        'selected_term_id': selected_term_id,
        'selected_semester_id': selected_semester_id,
        'student': student,
    })

#display total grade
@login_required
def studentTotalScoreForActivityType(request):
    is_teacher = request.user.profile.role.name.lower() == 'teacher'
    students = CustomUser.objects.filter(profile__role__name__iexact='student')  
    return render(request, 'gradebookcomponent/activityGrade/studentTotalActivityScore.html', {
        'is_teacher': is_teacher,
        'students': students,  
    })

# Teacher (fetch student total score for all activity)
@login_required
def studentTotalScoreApi(request):
    selected_semester_id = request.GET.get('semester', None)
    current_semester = None

    if selected_semester_id == 'current' or not selected_semester_id:
        current_semester = get_current_semester(request)
        if not current_semester:
            return JsonResponse({'error': 'No current semester found.'}, status=400)
    else:
        try:
            current_semester = Semester.objects.get(id=selected_semester_id)
        except Semester.DoesNotExist:
            return JsonResponse({'error': 'Selected semester not found.'}, status=400)

    user = request.user
    is_teacher = user.profile.role.name.lower() == 'teacher'
    is_student = user.profile.role.name.lower() == 'student'

    if is_teacher:
        students = CustomUser.objects.filter(profile__role__name__iexact='student')
        subjects = Subject.objects.filter(assign_teacher=user, subjectenrollment__semester=current_semester).distinct()
    elif is_student:
        students = CustomUser.objects.filter(id=user.id)
        subjects = Subject.objects.filter(subjectenrollment__student=user, subjectenrollment__semester=current_semester).distinct()
    else:
        return JsonResponse({'error': 'Unauthorized access.'}, status=403)

    selected_subject_id = request.GET.get('subject', 'all')

    if selected_subject_id != 'all':
        subjects = subjects.filter(id=selected_subject_id)

    # Use student IDs as keys to avoid serialization errors
    student_data = defaultdict(lambda: defaultdict(list))
    student_total_weighted_grade = defaultdict(lambda: defaultdict(Decimal))
    remedial_data = defaultdict(lambda: defaultdict(list))

    # Loop through each term
    for term in Term.objects.filter(semester=current_semester):
        for subject in subjects:
            if is_student:
                subject_enrollment = SubjectEnrollment.objects.filter(student=user, subject=subject, semester=current_semester).first()
                if not subject_enrollment or not subject_enrollment.can_view_grade:
                    continue

            student_scores = defaultdict(lambda: {'term_scores': [], 'total_weighted_score': Decimal(0)})

            try:
                term_gradebook_component = TermGradeBookComponents.objects.get(
                    term=term,
                    subjects=subject
                )
                term_percentage = Decimal(term_gradebook_component.percentage)
            except TermGradeBookComponents.DoesNotExist:
                term_percentage = Decimal(0)

            # Regular activities (non-remedial)
            for activity_type in ActivityType.objects.all():
                activities = Activity.objects.filter(term=term, activity_type=activity_type, subject=subject, remedial=False)

                try:
                    gradebook_component = GradeBookComponents.objects.get(
                        teacher=user if is_teacher else subject.assign_teacher,
                        subject=subject,
                        activity_type=activity_type
                    )
                    activity_percentage = Decimal(gradebook_component.percentage)
                except GradeBookComponents.DoesNotExist:
                    activity_percentage = Decimal(0)

                for student in students:
                    if not student.subjectenrollment_set.filter(subject=subject, semester=current_semester).exists():
                        continue

                    student_total_score = Decimal(0)
                    max_score_sum = Decimal(0)

                    for activity in activities:
                        student_questions = StudentQuestion.objects.filter(
                            student=student,
                            activity_question__activity=activity,
                            status=True
                        )

                        if not student_questions.exists():
                            max_score = activity.activityquestion_set.aggregate(total_max_score=Sum('score'))['total_max_score'] or Decimal(0)
                            max_score_sum += Decimal(max_score)
                            student_scores[student]['term_scores'].append({
                                'term_name': term.term_name,
                                'activity_type': activity_type.name,
                                'term_final_score': Decimal(0),
                                'missed': True
                            })
                            continue

                        for student_question in student_questions:
                            score = Decimal(student_question.score)
                            max_score = Decimal(student_question.activity_question.score)

                            student_total_score += score
                            max_score_sum += max_score

                    if max_score_sum > 0:
                        weighted_score = (student_total_score / max_score_sum) * activity_percentage
                        student_scores[student]['term_scores'].append({
                            'term_name': term.term_name,
                            'activity_type': activity_type.name,
                            'term_final_score': weighted_score,
                        })
                        student_scores[student]['total_weighted_score'] += weighted_score

            # Participation activities
            participation_activity_type = ActivityType.objects.get(name__iexact="Participation")
            participation_activities = Activity.objects.filter(term=term, activity_type=participation_activity_type, subject=subject, remedial=False)

            try:
                participation_component = GradeBookComponents.objects.get(
                    teacher=user if is_teacher else subject.assign_teacher,
                    subject=subject,
                    activity_type=participation_activity_type
                )
                participation_percentage = Decimal(participation_component.percentage)
            except GradeBookComponents.DoesNotExist:
                participation_percentage = Decimal(0)

            for student in students:
                if not student.subjectenrollment_set.filter(subject=subject, semester=current_semester).exists():
                    continue

                participation_total_score = Decimal(0)
                participation_max_score_sum = Decimal(0)

                # Fetch participation data directly from StudentQuestion where is_participation=True
                participation_student_questions = StudentQuestion.objects.filter(
                    student=student,
                    activity__term=term,
                    activity__subject=subject,
                    is_participation=True
                )

                for student_question in participation_student_questions:
                    score = Decimal(student_question.score)
                    participation_total_score += score
                    participation_max_score_sum += 100  # Assuming the max score for participation is 100

                if participation_max_score_sum > 0:
                    participation_weighted_score = (participation_total_score / participation_max_score_sum) * participation_percentage
                    student_scores[student]['term_scores'].append({
                        'term_name': term.term_name,
                        'activity_type': participation_activity_type.name,
                        'term_final_score': participation_weighted_score,
                    })
                    student_scores[student]['total_weighted_score'] += participation_weighted_score

            # Process remedial activities separately
            remedial_activities = Activity.objects.filter(term=term, subject=subject, remedial=True)

            for activity in remedial_activities:
                for remedial_student in activity.remedial_students.all():
                    if remedial_student not in students:
                        continue

                    student_questions = StudentQuestion.objects.filter(
                        student=remedial_student,
                        activity_question__activity=activity,
                        status=True
                    )

                    # Check for matching sub_gradebook_component
                    sub_gradebook_component = SubGradeBook.objects.filter(gradebook__activity_type=activity.activity_type).first()
                    if sub_gradebook_component:
                        
                        for student_question in student_questions:
                            score = Decimal(student_question.score)
                            max_score = Decimal(student_question.activity_question.score)
                            weighted_score = (score / max_score) * Decimal(sub_gradebook_component.percentage)

                            # Store remedial data separately using student ID instead of the object
                            remedial_data[remedial_student.id][subject.subject_name].append({
                                'term_name': term.term_name,
                                'activity_name': activity.activity_name,
                                'weighted_score': weighted_score,
                                'max_score': max_score,
                                'percentage': (score / max_score) * 100 if max_score > 0 else 0,
                            })

                            # Add remedial points as bonus (does not change max score)
                            student_scores[remedial_student]['total_weighted_score'] += weighted_score

            # Calculate total weighted score (including regular, participation, and remedial bonus points)
            for student, scores in student_scores.items():
                weighted_term_score = scores['total_weighted_score'] * (term_percentage / Decimal(100))
                student_total_weighted_grade[student.id][subject.subject_name] += weighted_term_score

                max_possible_score = term_percentage
                weighted_term_percentage = (weighted_term_score / max_possible_score) * Decimal(100) if max_possible_score > 0 else Decimal(0)

                student_data[student.id][subject.subject_name].append({
                    'subject_id': subject.id,
                    'term_name': term.term_name,
                    'total_weighted_score': f"{weighted_term_score:.6f}",
                    'percentage': f"{weighted_term_percentage:.1f}%",
                    'missed': any(score.get('missed', False) for score in scores['term_scores']),
                    'student_name': student.get_full_name()
                })

    return JsonResponse({
        'student_data': student_data,
        'remedial_data': remedial_data,
        'student_total_weighted_grade': student_total_weighted_grade
    })


@login_required
def getSemesters(request):
    semesters = Semester.objects.all().order_by('-start_date')

    semesters_data = []
    for semester in semesters:
        semesters_data.append({
            'id': semester.id,
            'semester_name': semester.semester_name,
            'school_year': semester.school_year,
            'start_date': semester.start_date.strftime('%Y-%m-%d'),
            'end_date': semester.end_date.strftime('%Y-%m-%d'),
        })

    # Return the data as a JSON response
    return JsonResponse({'semesters': semesters_data})

# fetcH subject
@login_required
def getSubjects(request):
    semester_id = request.GET.get('semester_id')

    if not semester_id:
        return JsonResponse({'error': 'Semester ID not provided.'}, status=400)
    try:
        selected_semester = Semester.objects.get(id=semester_id)
    except Semester.DoesNotExist:
        return JsonResponse({'error': 'Selected semester not found.'}, status=404)

    user = request.user
    is_student = user.profile.role.name.lower() == 'student'

    if is_student:
        subjects = Subject.objects.filter(
            subjectenrollment__student=user, 
            subjectenrollment__semester=selected_semester
        ).values('id', 'subject_name')
    else:
        subjects = Subject.objects.filter(
            assign_teacher=user, 
            subjectenrollment__semester=selected_semester
        ).values('id', 'subject_name')

    unique_subjects = {subject['id']: subject for subject in subjects}.values()
    subjects_list = list(unique_subjects)

    return JsonResponse({'subjects': subjects_list})

# Teacher (allow student to see grade)
@login_required
def allowGradeVisibility(request, student_id):
    if request.method == "POST":
        subject_id = request.POST.get('subject_id')
        can_view_grade = request.POST.get('can_view_grade') == 'true'

        # Filter instead of get, as there might be multiple enrollments
        subject_enrollments = SubjectEnrollment.objects.filter(student_id=student_id, subject_id=subject_id)

        if not subject_enrollments.exists():
            return JsonResponse({'status': 'failure', 'message': 'No enrollments found for this student and subject.'}, status=400)
        
        for enrollment in subject_enrollments:
            # Retrieve the subject name
            subject_name = enrollment.subject.subject_name

            # Update the visibility status
            enrollment.can_view_grade = can_view_grade
            enrollment.save()

        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'failure'}, status=400)



FAILING_THRESHOLD = Decimal(75)
EXCELLING_THRESHOLD = Decimal(85)

@login_required
def failingStudentsPerSubjectView(request):
    current_semester = get_current_semester(request)

    if current_semester is None:
        return render(request, 'gradebookcomponent/studentProgress/failingStudent.html', {
            'failing_students_summary': [],
            'current_semester': 'No current semester available'
        })

    user = request.user
    is_teacher = user.profile.role.name.lower() == 'teacher'
    is_student = user.profile.role.name.lower() == 'student'

    # Admin or other non-teacher/non-student users should see all students and subjects
    if not is_teacher and not is_student:
        students = CustomUser.objects.filter(profile__role__name__iexact='student')
        subjects = Subject.objects.filter(subjectenrollment__semester=current_semester).distinct()
    elif is_teacher:
        students = CustomUser.objects.filter(profile__role__name__iexact='student')
        subjects = Subject.objects.filter(assign_teacher=user, subjectenrollment__semester=current_semester).distinct()
    elif is_student:
        students = CustomUser.objects.filter(id=user.id)
        subjects = Subject.objects.filter(subjectenrollment__student=user, subjectenrollment__semester=current_semester).distinct()
    else:
        return render(request, '404.html', {'error': 'Unauthorized access'})

    subject_failing_students = defaultdict(lambda: defaultdict(list))  # Group by subject and term
    unique_failing_students = defaultdict(set)  # Set to track unique failing students per subject

    for term in Term.objects.filter(semester=current_semester):
        for subject in subjects:
            for student in students:
                subject_enrollment = SubjectEnrollment.objects.filter(student=student, subject=subject, semester=current_semester).first()

                if not subject_enrollment or not subject_enrollment.can_view_grade:
                    continue

                student_scores = defaultdict(lambda: {'total_weighted_score': Decimal(0)})

                # Calculate participation score
                participation_component = GradeBookComponents.objects.filter(
                    teacher=user if is_teacher else subject.assign_teacher,
                    subject=subject,
                    is_participation=True
                ).first()

                if participation_component:
                    participation_score = StudentParticipationScore.objects.filter(
                        student=student, subject=subject, term=term
                    ).first()

                    if participation_score:
                        weighted_participation_score = (Decimal(participation_score.score) / Decimal(participation_score.max_score)) * Decimal(participation_component.percentage)
                        student_scores[student]['total_weighted_score'] += weighted_participation_score

                # Calculate activity scores
                for activity_type in ActivityType.objects.all():
                    activities = Activity.objects.filter(term=term, activity_type=activity_type, subject=subject)

                    gradebook_component = GradeBookComponents.objects.filter(
                        teacher=user if is_teacher else subject.assign_teacher,
                        subject=subject,
                        activity_type=activity_type
                    ).first()

                    if not gradebook_component:
                        continue

                    activity_percentage = Decimal(gradebook_component.percentage)
                    student_total_score = Decimal(0)
                    max_score_sum = Decimal(0)

                    for activity in activities:
                        student_questions = StudentQuestion.objects.filter(
                            student=student,
                            activity_question__activity=activity,
                            status=True
                        )

                        if not student_questions.exists():
                            max_score_sum += Decimal(activity.activityquestion_set.aggregate(total_max_score=Sum('score'))['total_max_score'] or Decimal(0))
                            continue

                        for student_question in student_questions:
                            score = Decimal(student_question.score)
                            max_score = Decimal(student_question.activity_question.score)

                            student_total_score += score
                            max_score_sum += max_score

                    if max_score_sum > 0:
                        weighted_score = (student_total_score / max_score_sum) * activity_percentage
                        student_scores[student]['total_weighted_score'] += weighted_score

                # If no participation or activity score exists, skip this student for this term
                if student_scores[student]['total_weighted_score'] == 0:
                    continue  # Skip this student for this term

                # Calculate the final weighted score considering the term percentage
                try:
                    term_gradebook_component = TermGradeBookComponents.objects.get(
                        term=term,
                        subjects=subject
                    )
                    term_percentage = Decimal(term_gradebook_component.percentage)
                except TermGradeBookComponents.DoesNotExist:
                    term_percentage = Decimal(0)

                weighted_term_score = student_scores[student]['total_weighted_score'] * (term_percentage / Decimal(100))
                
                # Convert the weighted term score to a percentage
                percentage_score = (weighted_term_score / term_percentage) * Decimal(100) if term_percentage > 0 else Decimal(0)

                # Check if the student meets the failing threshold based on percentage
                if percentage_score < FAILING_THRESHOLD:
                    # Track the student under the subject but only count them once per subject
                    unique_failing_students[subject.subject_name].add(student.id)

                    # Append the student details to the list of failing students under the term
                    subject_failing_students[subject.subject_name][term.term_name].append({
                        'student_name': student.get_full_name(),
                        'student_id': student.id,
                        'grade': percentage_score
                    })

    failing_students_summary = [
        {
            'subject_name': subject_name,
            'failing_students_count': len(unique_failing_students[subject_name]),  # Unique count
            'terms': dict(terms)  # Convert defaultdict to dict for easy iteration
        } for subject_name, terms in subject_failing_students.items()
    ]

    return render(request, 'gradebookcomponent/studentProgress/failingStudent.html', {
        'failing_students_summary': failing_students_summary,
        'current_semester': current_semester.semester_name
    })

@login_required
def excellingStudentsPerSubjectView(request):
    current_semester = get_current_semester(request)

    if current_semester is None:
        return render(request, 'gradebookcomponent/studentProgress/excellingStudent.html', {
            'excelling_students_summary': [],
            'current_semester': 'No current semester available'
        })

    user = request.user
    is_teacher = user.profile.role.name.lower() == 'teacher'
    is_student = user.profile.role.name.lower() == 'student'

    # Admin or other non-teacher/non-student users should see all students and subjects
    if not is_teacher and not is_student:
        students = CustomUser.objects.filter(profile__role__name__iexact='student')
        subjects = Subject.objects.filter(subjectenrollment__semester=current_semester).distinct()
    elif is_teacher:
        students = CustomUser.objects.filter(profile__role__name__iexact='student')
        subjects = Subject.objects.filter(assign_teacher=user, subjectenrollment__semester=current_semester).distinct()
    elif is_student:
        students = CustomUser.objects.filter(id=user.id)
        subjects = Subject.objects.filter(subjectenrollment__student=user, subjectenrollment__semester=current_semester).distinct()
    else:
        return render(request, '404.html', {'error': 'Unauthorized access'})

    subject_excelling_students = defaultdict(lambda: defaultdict(list))  # Group by subject and term
    unique_excelling_students = defaultdict(set)  # Set to track unique excelling students per subject

    for term in Term.objects.filter(semester=current_semester):
        for subject in subjects:
            for student in students:
                subject_enrollment = SubjectEnrollment.objects.filter(student=student, subject=subject, semester=current_semester).first()

                if not subject_enrollment or not subject_enrollment.can_view_grade:
                    continue

                student_scores = defaultdict(lambda: {'total_weighted_score': Decimal(0)})

                # Calculate participation score
                participation_component = GradeBookComponents.objects.filter(
                    teacher=user if is_teacher else subject.assign_teacher,
                    subject=subject,
                    is_participation=True
                ).first()

                if participation_component:
                    participation_score = StudentParticipationScore.objects.filter(
                        student=student, subject=subject, term=term
                    ).first()

                    if participation_score:
                        weighted_participation_score = (Decimal(participation_score.score) / Decimal(participation_score.max_score)) * Decimal(participation_component.percentage)
                        student_scores[student]['total_weighted_score'] += weighted_participation_score

                # Calculate activity scores
                for activity_type in ActivityType.objects.all():
                    activities = Activity.objects.filter(term=term, activity_type=activity_type, subject=subject)

                    gradebook_component = GradeBookComponents.objects.filter(
                        teacher=user if is_teacher else subject.assign_teacher,
                        subject=subject,
                        activity_type=activity_type
                    ).first()

                    if not gradebook_component:
                        continue

                    activity_percentage = Decimal(gradebook_component.percentage)
                    student_total_score = Decimal(0)
                    max_score_sum = Decimal(0)

                    for activity in activities:
                        student_questions = StudentQuestion.objects.filter(
                            student=student,
                            activity_question__activity=activity,
                            status=True
                        )

                        if not student_questions.exists():
                            max_score_sum += Decimal(activity.activityquestion_set.aggregate(total_max_score=Sum('score'))['total_max_score'] or Decimal(0))
                            continue

                        for student_question in student_questions:
                            score = Decimal(student_question.score)
                            max_score = Decimal(student_question.activity_question.score)

                            student_total_score += score
                            max_score_sum += max_score

                    if max_score_sum > 0:
                        weighted_score = (student_total_score / max_score_sum) * activity_percentage
                        student_scores[student]['total_weighted_score'] += weighted_score

                # Calculate the final weighted score considering the term percentage
                try:
                    term_gradebook_component = TermGradeBookComponents.objects.get(
                        term=term,
                        subjects=subject
                    )
                    term_percentage = Decimal(term_gradebook_component.percentage)
                except TermGradeBookComponents.DoesNotExist:
                    term_percentage = Decimal(0)

                weighted_term_score = student_scores[student]['total_weighted_score'] * (term_percentage / Decimal(100))
                
                # Convert the weighted term score to a percentage
                percentage_score = (weighted_term_score / term_percentage) * Decimal(100) if term_percentage > 0 else Decimal(0)

                # Check if the student meets the excelling threshold based on percentage
                if percentage_score >= EXCELLING_THRESHOLD:
                    # Track the student under the subject but only count them once per subject
                    unique_excelling_students[subject.subject_name].add(student.id)

                    # Append the student details to the list of excelling students under the term
                    subject_excelling_students[subject.subject_name][term.term_name].append({
                        'student_name': student.get_full_name(),
                        'student_id': student.id,
                        'grade': percentage_score
                    })

    excelling_students_summary = [
        {
            'subject_name': subject_name,
            'excelling_students_count': len(unique_excelling_students[subject_name]),  # Unique count
            'terms': dict(terms)  # Convert defaultdict to dict for easy iteration
        } for subject_name, terms in subject_excelling_students.items()
    ]

    return render(request, 'gradebookcomponent/studentProgress/excellingStudent.html', {
        'excelling_students_summary': excelling_students_summary,
        'current_semester': current_semester.semester_name
    })