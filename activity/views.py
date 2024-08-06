from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import Activity, ActivityType, StudentActivity, ActivityQuestion, QuizType, QuestionChoice
from subject.models import Subject
from accounts.models import CustomUser
from django.db.models import Sum

class AddActivityView(View):
    def get(self, request, subject_id):
        subject = get_object_or_404(Subject, id=subject_id)
        activity_types = ActivityType.objects.all()
        return render(request, 'activity/createActivity.html', {
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

        students = CustomUser.objects.filter(subjectenrollment__subjects=subject).distinct()
        for student in students:
            StudentActivity.objects.create(student=student, activity=activity)

        return redirect('add_quiz_type', activity_id=activity.id)


class AddQuizTypeView(View):
    def get(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        quiz_types = QuizType.objects.all()
        return render(request, 'activity/createQuizType.html', {
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
        return render(request, 'activity/createQuestion.html', {
            'activity': activity,
            'quiz_type': quiz_type,
            'questions': questions,
            'total_score': total_score
        })

    def post(self, request, activity_id, quiz_type_id):
        activity = get_object_or_404(Activity, id=activity_id)
        quiz_type = get_object_or_404(QuizType, id=quiz_type_id)
        question_text = request.POST.get('question_text')
        correct_answer_index = int(request.POST.get('correct_answer')) if quiz_type.name == 'Multiple Choice' else None
        score = request.POST.get('score')

        question = ActivityQuestion.objects.create(
            activity=activity,
            question_text=question_text,
            correct_answer='',  # Set to empty initially
            quiz_type=quiz_type,
            score=score
        )

        if quiz_type.name == 'Multiple Choice':
            choices = request.POST.getlist('choices')
            for index, choice_text in enumerate(choices):
                choice = QuestionChoice.objects.create(question=question, choice_text=choice_text)
                if index == correct_answer_index:
                    question.correct_answer = choice_text
            question.save()

        elif quiz_type.name != 'Essay':
            question.correct_answer = request.POST.get('correct_answer')
            question.save()

        return redirect('add_question', activity_id=activity.id, quiz_type_id=quiz_type.id)


class EditQuestionView(View):
    def get(self, request, question_id):
        question = get_object_or_404(ActivityQuestion, id=question_id)
        quiz_type = question.quiz_type
        return render(request, 'activity/editQuestion.html', {
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
        return render(request, 'activity/displayQuestion.html', {
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
            if question.quiz_type.name != 'Essay':
                is_correct = (answer == question.correct_answer)
                total_score += question.score if is_correct else 0
            student_activity.score = total_score
            student_activity.status = True  # Mark the activity as completed
            student_activity.save()
        return redirect('activity_completed', score=int(total_score))


def activityCompletedView(request, score):
    return render(request, 'activity/activityCompleted.html', {'score': score})
    

