from django.shortcuts import render, redirect, get_object_or_404
from .forms import GradeBookComponentsForm, CopyGradeBookForm, TermGradeBookComponentsForm
from .models import GradeBookComponents, TermGradeBookComponents
from activity.models import StudentQuestion, Activity, ActivityQuestion, ActivityType
from accounts.models import CustomUser
from django.db.models import Sum, Max
from django.utils import timezone
from course.models import Semester, Term, StudentParticipationScore, SubjectEnrollment
from subject.models import Subject
from decimal import Decimal
from django.http import JsonResponse
from decimal import Decimal
from collections import defaultdict
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

#View GradeBookComponents
@login_required
def viewGradeBookComponents(request):
    gradebookcomponents = GradeBookComponents.objects.all()
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
            target_subject = form.cleaned_data['subject']
            
            # Copy all GradeBookComponents from source subject to target subject
            components_to_copy = GradeBookComponents.objects.filter(subject=source_subject, teacher=request.user)
            for component in components_to_copy:
                # Check if the component already exists in the target subject
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
            messages.success(request, 'An error occured while creating gradebook!')    
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

#View TermGradeBook List
@login_required
def termBookList(request):
    termbook = TermGradeBookComponents.objects.all()
    return render(request, 'gradebookcomponent/termbook/TermBook.html', {'termbook': termbook})

#create TermGradeBook
@login_required
def createTermGradeBookComponent(request):
    if request.method == 'POST':
        form = TermGradeBookComponentsForm(request.POST, user=request.user)
        if form.is_valid():
            instance = form.save(commit=False)  # Save the main model instance without committing
            instance.teacher = request.user 
            instance.save() 
            
            form.save_m2m()  
            messages.success(request, 'Termbook deleted successfully!')
            return redirect('termBookList')
        else:
            messages.success(request, 'An error occured while creating termbook!')
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
def viewTermBookComponent(request, id):
    termbook = get_object_or_404(TermGradeBookComponents, id=id)
    return render(request, 'gradebookcomponent/termbook/viewTermBook.html', {'termbook': termbook})

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
    selected_term_id = request.GET.get('term', 'all')

    # Fetch the student and subject based on IDs, filtering by the selected semester
    student = get_object_or_404(CustomUser, id=student_id)
    subject = get_object_or_404(Subject, id=subject_id, subjectenrollment__student=student, subjectenrollment__semester=current_semester)

    activity_types = ActivityType.objects.all()
    terms = Term.objects.filter(semester=current_semester)

    term_scores_data = []

    for term in terms:
        if selected_term_id != 'all' and str(term.id) != selected_term_id:
            continue
        
        student_scores_data = []
        term_has_data = False

        participation_component = GradeBookComponents.objects.filter(
            teacher=user, subject=subject, is_participation=True
        ).first()

        if participation_component:
            participation_score = StudentParticipationScore.objects.filter(
                student=student, subject=subject, term=term
            ).first()

            if participation_score:
                weighted_participation_score = (participation_score.score / participation_score.max_score) * participation_component.percentage
                term_has_data = True

                student_scores_data.append({
                    'student': student.get_full_name(),
                    'activity_name': 'Participation',
                    'question_text': 'Participation',
                    'total_score': participation_score.score,
                    'max_score': participation_score.max_score,
                    'percentage': (participation_score.score / participation_score.max_score) * 100,
                    'weighted_score': weighted_participation_score,
                    'activity': None,
                    'is_participation': True
                })

        for activity_type in activity_types:
            activities = Activity.objects.filter(term=term, activity_type=activity_type, subject=subject)

            try:
                gradebook_component = GradeBookComponents.objects.get(
                    teacher=user, 
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
                    student_scores_data.append({
                        'student': student.get_full_name(),
                        'activity_name': activity.activity_name,
                        'question_text': 'No submission',
                        'score': 0,
                        'max_score': 0,
                        'percentage': 0,
                        'weighted_score': 0,
                        'activity': activity.activity_name,
                        'missed': True,
                        'is_participation': False,
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
                        'activity': activity.activity_name,
                        'missed': False,
                        'is_participation': False,
                        'submission_time': student_question.submission_time,
                    })

                term_has_data = True

        if term_has_data:
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
    # Get the selected semester from the request (default to current semester if 'current' is provided)
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

    student_data = defaultdict(lambda: defaultdict(list))
    student_total_weighted_grade = defaultdict(lambda: defaultdict(Decimal))

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

            participation_component = GradeBookComponents.objects.filter(
                teacher=user if is_teacher else subject.assign_teacher, 
                subject=subject, 
                is_participation=True
            ).first()

            if participation_component:
                for student in students:
                    if not student.subjectenrollment_set.filter(subject=subject, semester=current_semester).exists():
                        continue

                    participation_score = StudentParticipationScore.objects.filter(
                        student=student, subject=subject, term=term
                    ).first()

                    if participation_score:
                        weighted_participation_score = (Decimal(participation_score.score) / Decimal(participation_score.max_score)) * Decimal(participation_component.percentage)
                        student_scores[student]['term_scores'].append({
                            'term_name': term.term_name,
                            'activity_type': 'Participation',
                            'term_final_score': weighted_participation_score
                        })
                        student_scores[student]['total_weighted_score'] += weighted_participation_score

            for activity_type in ActivityType.objects.all():
                activities = Activity.objects.filter(term=term, activity_type=activity_type, subject=subject)

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
                            'term_final_score': weighted_score
                        })
                        student_scores[student]['total_weighted_score'] += weighted_score

            for student, scores in student_scores.items():
                weighted_term_score = scores['total_weighted_score'] * (term_percentage / Decimal(100))
                student_total_weighted_grade[student][subject.subject_name] += weighted_term_score

                max_possible_score = term_percentage

                weighted_term_percentage = (weighted_term_score / max_possible_score) * Decimal(100) if max_possible_score > 0 else Decimal(0)

                student_data[student][subject.subject_name].append({
                    'term_name': term.term_name,
                    'total_weighted_score': f"{weighted_term_score:.6f}",
                    'percentage': f"{weighted_term_percentage:.1f}%",
                    'missed': any(score.get('missed', False) for score in scores['term_scores'])
                })

    final_term_data = []
    for student_obj, subjects in student_data.items():
        student_subjects = []
        student_id = student_obj.id

        for subject_name, terms in subjects.items():
            subject_id = Subject.objects.get(subject_name=subject_name).id
            student_subjects.append({
                'subject_name': subject_name,
                'subject_id': subject_id,
                'terms': terms,
                'total_weighted_grade': float(student_total_weighted_grade[student_obj][subject_name])
            })
        final_term_data.append({
            'student': student_obj.get_full_name(),
            'student_id': student_id,
            'subjects': student_subjects
        })

    return JsonResponse({'term_data': final_term_data})


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
    current_semester = get_current_semester(request)

    if not current_semester:
        return JsonResponse({'error': 'No current semester found.'}, status=400)

    user = request.user
    is_student = user.profile.role.name.lower() == 'student'

    if is_student:
        subjects = Subject.objects.filter(subjectenrollment__student=user, subjectenrollment__semester=current_semester).values('id', 'subject_name')
    else:
        subjects = Subject.objects.filter(assign_teacher=user, subjectenrollment__semester=current_semester).values('id', 'subject_name')

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


