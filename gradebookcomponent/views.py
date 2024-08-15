from django.shortcuts import render, redirect, get_object_or_404
from .forms import GradeBookComponentsForm, CopyGradeBookForm, TermGradeBookComponentsForm
from .models import GradeBookComponents, TermGradeBookComponents
from activity.models import StudentQuestion, Activity, ActivityQuestion, ActivityType, QuizType
from accounts.models import CustomUser
from django.db.models import Sum, Max
from django.utils import timezone
from course.models import Semester, Term
from subject.models import Subject
from decimal import Decimal
from django.http import JsonResponse
from decimal import Decimal
from collections import defaultdict
# Create your views here.

#View GradeBookComponents
def viewGradeBookComponents(request):
    gradebookcomponents = GradeBookComponents.objects.all()
    return render(request, 'gradebookcomponent/gradebook/gradeBook.html', {'gradebookcomponents': gradebookcomponents})


#Create GradeBookComponents
def createGradeBookComponents(request):
    if request.method == 'POST':
        form = GradeBookComponentsForm(request.POST, user=request.user)
        if form.is_valid():
            gradebook_component = form.save(commit=False)
            gradebook_component.teacher = request.user
            gradebook_component.save()
            return redirect('viewGradeBookComponents')
    else:
        form = GradeBookComponentsForm(user=request.user)
    
    return render(request, 'gradebookcomponent/gradebook/createGradeBook.html', {'form': form})

#Copy GradeBookComponents
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
            return redirect('viewGradeBookComponents')
    else:
        form = CopyGradeBookForm(user=request.user)
    
    return render(request, 'gradebookcomponent/gradebook/copyGradeBook.html', {'form': form})


#Modify GradeBookComponents
def updateGradeBookComponents(request, pk):
    gradebookcomponent = get_object_or_404(GradeBookComponents, pk=pk)
    if request.method == 'POST':
        form = GradeBookComponentsForm(request.POST, instance=gradebookcomponent)
        if form.is_valid():
            form.save()
            return redirect('viewGradeBookComponents')
    else:
        form = GradeBookComponentsForm(instance=gradebookcomponent)
    
    return render(request, 'gradebookcomponent/gradebook/updateGradeBook.html', {'form': form, 'gradebookcomponent':gradebookcomponent})

#Delete GradeBookComponents
def deleteGradeBookComponents(request, pk):
    gradebookcomponent = get_object_or_404(GradeBookComponents, pk=pk)
    gradebookcomponent.delete()
    return redirect('viewGradeBookComponents')

def termBookList(request):
    termbook = TermGradeBookComponents.objects.all()
    return render(request, 'gradebookcomponent/termbook/viewTermBook.html', {'termbook': termbook})


def createTermGradeBookComponent(request):
    if request.method == 'POST':
        form = TermGradeBookComponentsForm(request.POST, user=request.user)
        if form.is_valid():
            instance = form.save(commit=False)  # Save the main model instance without committing
            instance.teacher = request.user  # Ensure the teacher is assigned
            instance.save()  # Now save the instance to the database
            
            form.save_m2m()  # Save the ManyToMany relationships (subjects)

            for subject in instance.subjects.all():
                print(f"Saved: Teacher={instance.teacher.username}, Term={instance.term.term_name}, Subject={subject.subject_name}, Percentage={instance.percentage}%")
            
            return redirect('termBookList')
    else:
        form = TermGradeBookComponentsForm(user=request.user)

    return render(request, 'gradebookcomponent/termbook/createTermBook.html', {'form': form})





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

            question_details.append({
                'number': i,
                'question_text': question.activity_question.question_text,
                'correct_answer': question.activity_question.correct_answer,
                'student_answer': student_answer_display,
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


def get_current_semester():
    current_date = timezone.now().date()
    try:
        current_semester = Semester.objects.get(start_date__lte=current_date, end_date__gte=current_date)
        return current_semester
    except Semester.DoesNotExist:
        return None
    
def studentTotalScore(request):
    current_semester = get_current_semester()

    if not current_semester:
        return render(request, 'gradebookcomponent/studentTotalScore.html', {
            'error': 'No current semester found.'
        })

    user = request.user
    is_student = user.profile.role.name.lower() == 'student'

    if is_student:
        students = CustomUser.objects.filter(id=user.id)
        subjects = Subject.objects.filter(subjectenrollment__student=user)
    else:
        students = CustomUser.objects.filter(profile__role__name__iexact='student')
        subjects = Subject.objects.filter(assign_teacher=user)

    activity_types = ActivityType.objects.all()
    terms = Term.objects.filter(semester=current_semester)

    selected_term_id = request.GET.get('term', 'all')
    selected_subject_id = request.GET.get('subject', 'all')
    
    term_scores_data = []

    for term in terms:
        if selected_term_id != 'all' and str(term.id) != selected_term_id:
            continue
        
        for activity_type in activity_types:
            for subject in subjects:
                if selected_subject_id != 'all' and str(subject.id) != selected_subject_id:
                    continue

                student_scores_data = []
                term_total_score = Decimal(0)  # Initialize term total score for all students
                term_max_score = Decimal(0)  # Initialize term max score for the term
                total_weighted_score = Decimal(0)  # Initialize total weighted score for the term
                term_has_data = False

                activities = Activity.objects.filter(term=term, activity_type=activity_type, subject=subject)

                # Get the activity type percentage from GradeBookComponents
                try:
                    gradebook_component = GradeBookComponents.objects.get(
                        teacher=user, 
                        subject=subject, 
                        activity_type=activity_type
                    )
                    activity_percentage = gradebook_component.percentage
                except GradeBookComponents.DoesNotExist:
                    activity_percentage = Decimal(0)

                for student in students:
                    if not student.subjectenrollment_set.filter(subject=subject).exists():
                        continue

                    student_total_score = Decimal(0)  # Initialize student total score for this term
                    max_score_sum = Decimal(0)  # Initialize total max score for all activities

                    for activity in activities:
                        student_questions = StudentQuestion.objects.filter(
                            student=student,
                            activity_question__activity=activity,
                            status=True 
                        )
                        
                        total_score = student_questions.aggregate(total_score=Sum('score'))['total_score'] or 0
                        max_score = ActivityQuestion.objects.filter(activity=activity).aggregate(max_score=Sum('score'))['max_score'] or 0
                        
                        # Convert total_score to Decimal
                        total_score = Decimal(total_score)
                        max_score_sum += Decimal(max_score)  # Sum up max scores for all activities

                        student_total_score += total_score  # Accumulate student's total score for this term

                        if activity.end_time < timezone.now() and not student_questions.exists():
                            term_has_data = True
                            student_scores_data.append({
                                'student': student,
                                'total_score': 0,
                                'max_score': max_score or Decimal(0),
                                'percentage': 0,
                                'weighted_score': 0,
                                'activity': activity,
                                'missed': True
                            })
                        elif total_score > 0:
                            term_has_data = True
                            student_scores_data.append({
                                'student': student,
                                'total_score': total_score,
                                'max_score': max_score,
                                'percentage': (total_score / Decimal(max_score) * 100) if max_score > 0 else Decimal(0),
                                'weighted_score': (total_score / Decimal(max_score) * activity_percentage) if max_score > 0 else Decimal(0),
                                'activity': activity,
                                'missed': False
                            })

                    # After looping through all activities for this student, add their total score
                    if term_has_data:
                        total_percentage = (student_total_score / max_score_sum * 100) if max_score_sum > 0 else Decimal(0)
                        total_weighted_score = total_percentage * activity_percentage / 100

                        student_scores_data.append({
                            'student': student,
                            'total_score': student_total_score,  # Total score for this student in this term
                            'max_score': max_score_sum,  # The total max score possible in this term
                            'percentage': total_percentage,
                            'weighted_score': total_weighted_score,  # The weighted score for this student in this term
                            'activity': None,
                            'missed': False
                        })

                if term_has_data:
                    term_scores_data.append({
                        'term': term,
                        'activity_type': activity_type,
                        'subject': subject,
                        'student_scores_data': student_scores_data,
                        'term_total_score': term_total_score,  # The sum of all student scores for this term
                        'term_max_score': term_max_score,  # The sum of all possible max scores for this term
                    })

    return render(request, 'gradebookcomponent/activityGrade/studentGrade.html', {
        'current_semester': current_semester,
        'terms': terms,
        'subjects': subjects,
        'term_scores_data': term_scores_data,
        'selected_term_id': selected_term_id,
        'selected_subject_id': selected_subject_id,
    })


def studentTotalScoreForActivityType(request):
    return render(request, 'gradebookcomponent/activityGrade/studentTotalActivityScore.html')



def studentTotalScoreApi(request):
    current_semester = get_current_semester()

    if not current_semester:
        return JsonResponse({'error': 'No current semester found.'}, status=400)

    user = request.user
    is_student = user.profile.role.name.lower() == 'student'

    if is_student:
        students = CustomUser.objects.filter(id=user.id)
        subjects = Subject.objects.filter(subjectenrollment__student=user)
    else:
        students = CustomUser.objects.filter(profile__role__name__iexact='student')
        subjects = Subject.objects.filter(assign_teacher=user)

    activity_types = ActivityType.objects.all()
    terms = Term.objects.filter(semester=current_semester)

    selected_term_id = request.GET.get('term', 'all')
    selected_subject_id = request.GET.get('subject', 'all')
    
    # Filter terms based on selected term ID
    if selected_term_id != 'all':
        terms = terms.filter(id=selected_term_id)

    # Filter subjects based on selected subject ID
    if selected_subject_id != 'all':
        subjects = subjects.filter(id=selected_subject_id)

    term_data = {}

    for term in terms:
        term_name = term.term_name  # Assuming your Term model has a 'term_name' field
        aggregated_data = defaultdict(lambda: defaultdict(lambda: {'total_score': Decimal(0), 'weighted_score': Decimal(0)}))
        total_weighted_scores = defaultdict(Decimal)

        for activity_type in activity_types:
            for subject in subjects:
                # Get the activity type percentage from GradeBookComponents
                try:
                    gradebook_component = GradeBookComponents.objects.get(
                        teacher=user, 
                        subject=subject, 
                        activity_type=activity_type
                    )
                    activity_percentage = gradebook_component.percentage
                except GradeBookComponents.DoesNotExist:
                    activity_percentage = Decimal(0)

                for student in students:
                    if not student.subjectenrollment_set.filter(subject=subject).exists():
                        continue

                    total_score_sum = Decimal(0)
                    max_score_sum = Decimal(0)

                    activities = Activity.objects.filter(term=term, activity_type=activity_type, subject=subject)

                    for activity in activities:
                        student_questions = StudentQuestion.objects.filter(
                            student=student,
                            activity_question__activity=activity,
                            status=True 
                        )
                        
                        total_score = student_questions.aggregate(total_score=Sum('score'))['total_score'] or 0
                        max_score = ActivityQuestion.objects.filter(activity=activity).aggregate(max_score=Sum('score'))['max_score'] or 0
                        
                        total_score_sum += Decimal(total_score)
                        max_score_sum += Decimal(max_score)

                    # Calculate percentage and weighted score for the student
                    total_percentage = (total_score_sum / max_score_sum * 100) if max_score_sum > 0 else Decimal(0)
                    weighted_score = total_percentage * activity_percentage / 100

                    # Aggregate the results for each student and activity type within this term
                    aggregated_data[student.get_full_name()][activity_type.name]['total_score'] += total_score_sum
                    aggregated_data[student.get_full_name()][activity_type.name]['weighted_score'] += weighted_score
                    total_weighted_scores[student.get_full_name()] += weighted_score

        # Store the aggregated data for this term only
        term_data[term_name] = []

        for student, activities in aggregated_data.items():
            student_data = {
                'student': student,
                'activities': {}
            }
            for activity_type, scores in activities.items():
                student_data['activities'][activity_type] = {
                    'total_score': float(scores['total_score']),
                    'weighted_score': float(scores['weighted_score'])
                }
            student_data['total_weighted_score'] = float(total_weighted_scores[student])
            term_data[term_name].append(student_data)

    # Return the term data with all aggregated information
    return JsonResponse({'term_data': term_data}, safe=False)


def get_terms(request):
    current_semester = get_current_semester()
    
    if not current_semester:
        return JsonResponse({'error': 'No current semester found.'}, status=400)

    terms = Term.objects.filter(semester=current_semester).values('id', 'term_name')
    terms_list = list(terms)
    
    return JsonResponse({'terms': terms_list})