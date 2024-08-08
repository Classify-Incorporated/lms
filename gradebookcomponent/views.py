from django.shortcuts import render, redirect, get_object_or_404
from .forms import GradeBookComponentsForm
from .models import GradeBookComponents
from activity.models import StudentQuestion, Activity, ActivityQuestion
from accounts.models import CustomUser
from django.db.models import Sum
# Create your views here.

#View GradeBookComponents
def viewGradeBookComponents(request):
    gradebookcomponents = GradeBookComponents.objects.all()
    return render(request, 'gradebookcomponent/gradeBook.html', {'gradebookcomponents': gradebookcomponents})


#Create GradeBookComponents
def createGradeBookComponents(request):
    if request.method == 'POST':
        form = GradeBookComponentsForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('courseList')
    else:
        form = GradeBookComponentsForm()
    
    return render(request, 'gradebookcomponent/createGradeBook.html', {'form': form})

#Modify GradeBookComponents
def updateGradeBookComponents(request, pk):
    gradebookcomponent = get_object_or_404(GradeBookComponents, pk=pk)
    if request.method == 'POST':
        form = GradeBookComponentsForm(request.POST, instance=gradebookcomponent)
        if form.is_valid():
            form.save()
            return redirect('courseList')
    else:
        form = GradeBookComponentsForm(instance=gradebookcomponent)
    
    return render(request, 'gradebookcomponent/updateGradeBook.html', {'form': form})

#Delete GradeBookComponents
def deleteGradeBookComponents(request, pk):
    gradebookcomponent = get_object_or_404(GradeBookComponents, pk=pk)
    gradebookcomponent.delete()
    return redirect('viewGradeBookComponents')

#View GradeBookComponents
def viewGradeBookComponents(request):
    gradebookcomponents = GradeBookComponents.objects.all()
    return render(request, 'gradebookcomponent/viewGradeBook.html', {'gradebookcomponents': gradebookcomponents})



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
        student_scores_with_names.append({
            'student': student,
            'total_score': entry['total_score'],
            'max_score': max_score
        })

    return render(request, 'gradebookcomponent/finishedActivity.html', {
        'activity': activity,
        'student_scores': student_scores_with_names
    })


def studentActivityView(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    user = request.user

    if user.profile.role.name.lower() == 'student':
        student_scores = StudentQuestion.objects.filter(
            activity_question__activity=activity, student=user, score__gt=0
        ).values('student').annotate(total_score=Sum('score'))
    else:  # Assume the user is a teacher
        student_scores = StudentQuestion.objects.filter(
            activity_question__activity=activity, score__gt=0
        ).values('student').annotate(total_score=Sum('score'))

    detailed_scores = []
    for student_score in student_scores:
        student = get_object_or_404(CustomUser, id=student_score['student'])
        questions = StudentQuestion.objects.filter(student=student, activity_question__activity=activity, score__gt=0)
        max_score = ActivityQuestion.objects.filter(activity=activity).aggregate(total_score=Sum('score'))['total_score'] or 0
        question_details = []
        for i, question in enumerate(questions, start=1):
            question_details.append({
                'number': i,
                'question_text': question.activity_question.question_text,
                'correct_answer': question.activity_question.correct_answer,
                'student_answer': question.student_answer,
            })
        detailed_scores.append({
            'student': student,
            'total_score': student_score['total_score'],
            'max_score': max_score,
            'questions': question_details
        })

    return render(request, 'gradebookcomponent/detailedfinishActivity.html', {
        'activity': activity,
        'detailed_scores': detailed_scores
    })