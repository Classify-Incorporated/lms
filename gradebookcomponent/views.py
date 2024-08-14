from django.shortcuts import render, redirect, get_object_or_404
from .forms import GradeBookComponentsForm
from .models import GradeBookComponents
from activity.models import StudentQuestion, Activity, ActivityQuestion, ActivityType, QuizType
from accounts.models import CustomUser
from django.db.models import Sum, Max
from django.utils import timezone
from course.models import Semester, Term
from subject.models import Subject
from decimal import Decimal
# Create your views here.

#View GradeBookComponents
def viewGradeBookComponents(request):
    gradebookcomponents = GradeBookComponents.objects.all()
    return render(request, 'gradebookcomponent/gradebook/gradeBook.html', {'gradebookcomponents': gradebookcomponents})


#Create GradeBookComponents
def createGradeBookComponents(request):
    if request.method == 'POST':
        form = GradeBookComponentsForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('viewGradeBookComponents')
    else:
        form = GradeBookComponentsForm()
    
    return render(request, 'gradebookcomponent/gradebook/createGradeBook.html', {'form': form})

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


def calculate_student_grade(student_id):
    student_questions = StudentQuestion.objects.filter(student_id=student_id)
    total_score = sum(question.score for question in student_questions)
    return total_score


def student_grade_view(request):
    students = CustomUser.objects.filter(profile__role__name__iexact='student')
    students_grades = []

    for student in students:
        total_grade = calculate_student_grade(student.id)
        students_grades.append({
            'student': student,
            'total_grade': total_grade
        })

    return render(request, 'gradebookcomponent/displayGrade.html', {'students_grades': students_grades})


def all_students_activity_scores_view(request):
    students = CustomUser.objects.filter(profile__role__name__iexact='student')
    student_activity_scores = []
    finished_activities = []

    for student in students:
        activities = Activity.objects.filter(studentactivity__student=student)
        for activity in activities:
            questions = ActivityQuestion.objects.filter(activity=activity)
            max_score = questions.aggregate(total_score=Sum('score'))['total_score'] or 0

            total_score = sum(
                StudentQuestion.objects.get(student=student, activity_question=question).score
                for question in questions
            )

            student_activity_scores.append({
                'student': student,
                'activity': activity,
                'total_score': total_score,
                'max_score': max_score
            })

            # Check if the activity is finished (all questions graded)
            if all(StudentQuestion.objects.filter(activity_question=question, student=student).exists() for question in questions):
                finished_activities.append(activity)

    return render(request, 'gradebookcomponent/allStudentActivity.html', {
        'student_activity_scores': student_activity_scores,
        'finished_activities': finished_activities
    })


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

    return render(request, 'gradebookcomponent/finishedActivity.html', {
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

    return render(request, 'gradebookcomponent/detailedFinishActivity.html', {
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
        return render(request, 'gradebookcomponent/allStudentTotalScores.html', {
            'error': 'No current semester found.'
        })

    students = CustomUser.objects.filter(profile__role__name__iexact='student')
    activity_types = ActivityType.objects.all()
    subjects = Subject.objects.all()
    
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
                term_has_data = False

                gradebook_component = GradeBookComponents.objects.filter(activity_type=activity_type).first()
                component_percentage = gradebook_component.percentage if gradebook_component else Decimal(0)

                for student in students:
                    if not student.subjectenrollment_set.filter(subject=subject).exists():
                        continue

                    activities = Activity.objects.filter(term=term, activity_type=activity_type, subject=subject)

                    for activity in activities:
                        student_questions = StudentQuestion.objects.filter(
                            student=student,
                            activity_question__activity=activity,
                            status=True 
                        )
                        
                        total_score = student_questions.aggregate(total_score=Sum('score'))['total_score'] or 0
                        max_score = student_questions.aggregate(max_score=Sum('activity_question__score'))['max_score'] or 0
                        percentage = Decimal(total_score / max_score * 100) if max_score > 0 else Decimal(0)
                        weighted_score = (percentage * component_percentage / 100) if component_percentage > 0 else Decimal(0)

                        if activity.end_time < timezone.now() and not student_questions.exists():
                            term_has_data = True
                            student_scores_data.append({
                                'student': student,
                                'total_score': 0,
                                'max_score': max_score or 0,
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
                                'percentage': percentage,
                                'weighted_score': weighted_score,
                                'activity': activity,
                                'missed': False
                            })

                if term_has_data:
                    term_scores_data.append({
                        'term': term,
                        'activity_type': activity_type,
                        'subject': subject,
                        'student_scores_data': student_scores_data,
                    })

    return render(request, 'gradebookcomponent/studentTotalScore.html', {
        'current_semester': current_semester,
        'terms': terms,
        'subjects': subjects,
        'term_scores_data': term_scores_data,
        'selected_term_id': selected_term_id,
        'selected_subject_id': selected_subject_id,
    })