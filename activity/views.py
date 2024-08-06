from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import Activity, ActivityType, StudentActivity, ActivityQuestion, QuizType, QuestionChoice
from subject.models import Subject
from accounts.models import CustomUser
from course.models import Section
from django.db.models import Sum

class AddActivityView(View):
    def get(self, request, subject_id):
        subject = get_object_or_404(Subject, id=subject_id)
        activity_types = ActivityType.objects.all()
        return render(request, 'activity/activities/createActivity.html', {
            'subject': subject,
            'activity_types': activity_types
        })

    def post(self, request, subject_id):
        subject = get_object_or_404(Subject, id=subject_id)
        activity_name = request.POST.get('activity_name')
        activity_type_id = request.POST.get('activity_type')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        activity_type = get_object_or_404(ActivityType, id=activity_type_id)
        
        activity = Activity.objects.create(
            activity_name=activity_name,
            activity_type=activity_type,
            subject=subject,
            start_time=start_time,
            end_time=end_time
        )

        # Filter students only
        students = CustomUser.objects.filter(subjectenrollment__subjects=subject, profile__role__name__iexact='Student').distinct()
        for student in students:
            StudentActivity.objects.create(student=student, activity=activity)

        return redirect('add_quiz_type', activity_id=activity.id)


class AddQuizTypeView(View):
    def get(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        quiz_types = QuizType.objects.all()
        return render(request, 'activity/question/createQuizType.html', {
            'activity': activity,
            'quiz_types': quiz_types
        })

    def post(self, request, activity_id):
        quiz_type_id = request.POST.get('quiz_type')
        return redirect('add_question', activity_id=activity_id, quiz_type_id=quiz_type_id)


class AddQuestionView(View):
    def get(self, request, activity_id, quiz_type_id):
        activity = get_object_or_404(Activity, id=activity_id)
        quiz_type = get_object_or_404(QuizType, id=quiz_type_id)
        questions = ActivityQuestion.objects.filter(activity=activity)
        total_score = questions.aggregate(Sum('score'))['score__sum'] or 0
        return render(request, 'activity/question/createQuestion.html', {
            'activity': activity,
            'quiz_type': quiz_type,
            'questions': questions,
            'total_score': total_score
        })

    def post(self, request, activity_id, quiz_type_id):
        activity = get_object_or_404(Activity, id=activity_id)
        quiz_type = get_object_or_404(QuizType, id=quiz_type_id)
        question_text = request.POST.get('question_text') if quiz_type.name != 'Matching' else ''
        correct_answer = request.POST.get('correct_answer') if quiz_type.name not in ['Essay', 'Matching'] else ''
        score = request.POST.get('score')

        question = ActivityQuestion.objects.create(
            activity=activity,
            question_text=question_text,
            correct_answer=correct_answer,
            quiz_type=quiz_type,
            score=score
        )

        if quiz_type.name == 'Multiple Choice':
            choices = request.POST.getlist('choices')
            correct_answer_index = int(request.POST.get('correct_answer'))
            for index, choice_text in enumerate(choices):
                choice = QuestionChoice.objects.create(question=question, choice_text=choice_text)
                if index == correct_answer_index:
                    question.correct_answer = choice_text
            question.save()

        elif quiz_type.name == 'Matching':
            left_side = request.POST.getlist('matching_left')
            right_side = request.POST.getlist('matching_right')
            for left, right in zip(left_side, right_side):
                QuestionChoice.objects.create(question=question, choice_text=f"{left} -> {right}")
            question.correct_answer = ", ".join(f"{left} -> {right}" for left, right in zip(left_side, right_side))
            question.save()

        return redirect('add_question', activity_id=activity.id, quiz_type_id=quiz_type.id)


class EditQuestionView(View):
    def get(self, request, question_id):
        question = get_object_or_404(ActivityQuestion, id=question_id)
        quiz_type = question.quiz_type
        return render(request, 'activity/question/updateQuestion.html', {
            'question': question,
            'quiz_type': quiz_type
        })

    def post(self, request, question_id):
        question = get_object_or_404(ActivityQuestion, id=question_id)
        question_text = request.POST.get('question_text')
        correct_answer = request.POST.get('correct_answer') if question.quiz_type.name != 'Essay' else ''
        score = request.POST.get('score')

        question.question_text = question_text
        question.correct_answer = correct_answer
        question.score = score
        question.save()

        if question.quiz_type.name == 'Multiple Choice':
            question.choices.all().delete()
            choices = request.POST.getlist('choices')
            for choice_text in choices:
                QuestionChoice.objects.create(question=question, choice_text=choice_text)

        return redirect('add_question', activity_id=question.activity.id, quiz_type_id=question.quiz_type.id)
    

class DisplayQuestionsView(View):
    def get(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        questions = ActivityQuestion.objects.filter(activity=activity)

        # Prepare data for matching type questions
        for question in questions:
            if question.quiz_type.name == 'Matching':
                pairs = question.correct_answer.split(", ")
                question.pairs = [{"left": pair.split(" -> ")[0], "right": pair.split(" -> ")[1]} for pair in pairs]

        return render(request, 'activity/question/displayQuestion.html', {
            'activity': activity,
            'questions': questions
        })


class SubmitAnswersView(View):
    def post(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        student = request.user
        total_score = 0
        
        for question in ActivityQuestion.objects.filter(activity=activity):
            answer = request.POST.get(f'question_{question.id}')
            student_activity, created = StudentActivity.objects.get_or_create(student=student, activity=activity)
            
            if question.quiz_type.name == 'Essay':
                student_activity.essay_answer = answer
                student_activity.status = False  # Essays need manual grading
            elif question.quiz_type.name == 'Matching':
                pairs = question.correct_answer.split(", ")
                correct_answers = {pair.split(" -> ")[0]: pair.split(" -> ")[1] for pair in pairs}
                answers = {key: request.POST.get(f'question_{question.id}_{key}') for key in correct_answers.keys()}
                is_correct = all(correct_answers[k] == answers[k] for k in correct_answers)
                if is_correct:
                    total_score += question.score
                    student_activity.score += question.score  # Update the score for the student activity
                student_activity.status = True  # Non-essay questions are graded directly
            else:
                is_correct = (answer == question.correct_answer)
                if is_correct:
                    total_score += question.score
                    student_activity.score += question.score  # Update the score for the student activity
                student_activity.status = True  # Non-essay questions are graded directly
            
            student_activity.save()
        
        return redirect('activity_completed', score=int(total_score))


def activityCompletedView(request, score):
    return render(request, 'activity/activities/activityCompleted.html', {'score': score})
    

class GradeEssayView(View):
    def get(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        student_activities = StudentActivity.objects.filter(activity=activity, status=False, essay_answer__isnull=False)
        essay_questions = ActivityQuestion.objects.filter(activity=activity, quiz_type__name='Essay')
        return render(request, 'activity/grade/gradeEssay.html', {
            'activity': activity,
            'student_activities': student_activities,
            'essay_questions': essay_questions
        })

    def post(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        student_activities = StudentActivity.objects.filter(activity=activity, status=False, essay_answer__isnull=False)

        for student_activity in student_activities:
            score = request.POST.get(f'score_{student_activity.id}')
            if score:
                student_activity.score = float(score)
                student_activity.status = True 
                student_activity.save()

        return redirect('activity_completed', score=0)
    

def studentQuizzesExams(request):
    teacher = request.user

    # Get sections where the teacher is assigned
    sections = Section.objects.filter(assign_teacher=teacher)
    subjects = Subject.objects.filter(section__in=sections).distinct()

    # Get activities for these subjects
    activities = Activity.objects.filter(subject__in=subjects).distinct()

    activity_details = []

    for activity in activities:
        student_activities = StudentActivity.objects.filter(activity=activity).select_related('student', 'activity', 'activity__subject')

        for student_activity in student_activities:
            section = Section.objects.filter(subjects=student_activity.activity.subject, assign_teacher=teacher).first()
            activity_detail = {
                'activity': student_activity.activity,
                'subject': student_activity.activity.subject.subject_name,
                'student': student_activity.student,
                'score': student_activity.score,
                'section': section.section_name if section else 'N/A',  # Include section name
            }
            print(f"Activity Detail: {activity_detail}")  # Debugging line
            activity_details.append(activity_detail)

    print(f"Total activities to display: {len(activity_details)}")

    return render(request, 'activity/activities/allActivity.html', {'activity_details': activity_details})