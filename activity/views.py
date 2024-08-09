from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import Activity, ActivityType, StudentActivity, ActivityQuestion, QuizType, QuestionChoice, StudentQuestion
from subject.models import Subject
from accounts.models import CustomUser
from course.models import Section, Term
from django.db.models import Sum
from django.db.models import Max
from django.utils import timezone

class AddActivityView(View):
    def get(self, request, subject_id):
        subject = get_object_or_404(Subject, id=subject_id)
        activity_types = ActivityType.objects.all()
        terms = Term.objects.filter(semester__subjectenrollment__subjects=subject).distinct()
        return render(request, 'activity/activities/createActivity.html', {
            'subject': subject,
            'activity_types': activity_types,
            'terms': terms
        })

    def post(self, request, subject_id):
        subject = get_object_or_404(Subject, id=subject_id)
        activity_name = request.POST.get('activity_name')
        activity_type_id = request.POST.get('activity_type')
        term_id = request.POST.get('term')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        activity_type = get_object_or_404(ActivityType, id=activity_type_id)
        term = get_object_or_404(Term, id=term_id)
        
        activity = Activity.objects.create(
            activity_name=activity_name,
            activity_type=activity_type,
            subject=subject,
            term=term,
            start_time=start_time,
            end_time=end_time
        )

        # Filter students only
        students = CustomUser.objects.filter(subjectenrollment__subjects=subject, profile__role__name__iexact='Student').distinct()
        for student in students:
            StudentActivity.objects.create(student=student, activity=activity, term=term)

        return redirect('add_quiz_type', activity_id=activity.id)


class AddQuizTypeView(View):
    def get(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        quiz_types = QuizType.objects.all()
        questions = request.session.get('questions', {}).get(str(activity_id), [])
        return render(request, 'activity/question/createQuizType.html', {
            'activity': activity,
            'quiz_types': quiz_types,
            'questions': questions
        })

    def post(self, request, activity_id):
        quiz_type_id = request.POST.get('quiz_type')
        return redirect('add_question', activity_id=activity_id, quiz_type_id=quiz_type_id)


class AddQuestionView(View):
    def get(self, request, activity_id, quiz_type_id):
        activity = get_object_or_404(Activity, id=activity_id)
        quiz_type = get_object_or_404(QuizType, id=quiz_type_id)
        return render(request, 'activity/question/createQuestion.html', {
            'activity': activity,
            'quiz_type': quiz_type,
        })

    def post(self, request, activity_id, quiz_type_id):
        activity = get_object_or_404(Activity, id=activity_id)
        quiz_type = get_object_or_404(QuizType, id=quiz_type_id)

        question_text = request.POST.get('question_text', '')
        correct_answer = ''
        score = float(request.POST.get('score', 0))

        choices = []
        if quiz_type.name == 'Multiple Choice':
            choices = request.POST.getlist('choices')
            correct_answer_index = int(request.POST.get('correct_answer'))
            if correct_answer_index < len(choices):
                correct_answer = choices[correct_answer_index]

        if quiz_type.name == 'Matching':
            matching_left = request.POST.getlist('matching_left')
            matching_right = request.POST.getlist('matching_right')
            correct_answer = ", ".join([f"{left} -> {right}" for left, right in zip(matching_left, matching_right)])

        if quiz_type.name in ['True/False', 'Calculated Numeric', 'Fill in the Blank']:
            correct_answer = request.POST.get('correct_answer', '')

        question = {
            'question_text': question_text,
            'correct_answer': correct_answer,
            'quiz_type': quiz_type.name,
            'score': score,
            'choices': choices
        }

        questions = request.session.get('questions', {})
        if str(activity_id) not in questions:
            questions[str(activity_id)] = []
        questions[str(activity_id)].append(question)
        request.session['questions'] = questions

        return redirect('add_quiz_type', activity_id=activity.id)
    

class DeleteTempQuestionView(View):
    def post(self, request, activity_id, index):
        questions = request.session.get('questions', {})
        activity_questions = questions.get(str(activity_id), [])
        
        if index < len(activity_questions):
            del activity_questions[index]
        
        questions[str(activity_id)] = activity_questions
        request.session['questions'] = questions
        
        return redirect('add_quiz_type', activity_id=activity_id)
    

class SaveAllQuestionsView(View):
    def post(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        questions = request.session.get('questions', {}).get(str(activity_id), [])
        
        for question_data in questions:
            quiz_type = QuizType.objects.get(name=question_data['quiz_type'])
            question = ActivityQuestion.objects.create(
                activity=activity,
                question_text=question_data['question_text'],
                correct_answer=question_data['correct_answer'],
                quiz_type=quiz_type,
                score=question_data['score']
            )

            if quiz_type.name == 'Multiple Choice':
                for choice_text in question_data['choices']:
                    QuestionChoice.objects.create(question=question, choice_text=choice_text)

            # Create individual student questions
            students = CustomUser.objects.filter(subjectenrollment__subjects=activity.subject, profile__role__name__iexact='Student').distinct()
            for student in students:
                StudentQuestion.objects.create(student=student, activity_question=question)

        # Clear the questions from the session
        request.session.pop('questions', None)
        
        return redirect('courseList')
    

class DisplayQuestionsView(View):
    def get(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        student = request.user  # Assuming the user is a student
        questions = ActivityQuestion.objects.filter(activity=activity)

        # Prepare data for matching type questions
        for question in questions:
            if question.quiz_type.name == 'Matching':
                pairs = question.correct_answer.split(", ")
                question.pairs = []
                for pair in pairs:
                    if '->' in pair:
                        left, right = pair.split(" -> ")
                        question.pairs.append({"left": left, "right": right})

        # Debugging output
        print(f"User: {student.username}")
        print(f"Activity: {activity.activity_name}")
        for question in questions:
            print(f"Question: {question.question_text}")
            print(f"Quiz Type: {question.quiz_type.name}")
            if question.quiz_type.name == 'Matching':
                for pair in question.pairs:
                    print(f"Matching Pair: {pair['left']} -> {pair['right']}")
            elif question.quiz_type.name == 'Multiple Choice':
                for choice in question.choices.all():
                    print(f"Choice: {choice.choice_text}")

        return render(request, 'activity/question/displayQuestion.html', {
            'activity': activity,
            'questions': questions
        })

class SubmitAnswersView(View):
    def post(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        student = request.user
        total_score = 0
        has_non_essay_questions = False

        for question in ActivityQuestion.objects.filter(activity=activity):
            answer = request.POST.get(f'question_{question.id}')
            student_question, created = StudentQuestion.objects.get_or_create(student=student, activity_question=question)
            student_question.student_answer = answer

            if question.quiz_type.name == 'Essay':
                student_question.status = False  # Essays need manual grading
            else:
                is_correct = (answer == question.correct_answer)
                if is_correct:
                    total_score += question.score
                    student_question.score = question.score
                student_question.status = True  # Non-essay questions are graded directly
                has_non_essay_questions = True
            
            student_question.submission_time = timezone.now()  # Update the submission time
            student_question.save()

        student_activity, created = StudentActivity.objects.get_or_create(student=student, activity=activity)
        student_activity.save()

        return redirect('activity_completed', score=int(total_score), activity_id=activity_id, show_score=has_non_essay_questions)


def activityCompletedView(request, score, activity_id, show_score):
    activity = get_object_or_404(Activity, id=activity_id)
    max_score = activity.activityquestion_set.aggregate(total_score=Sum('score'))['total_score'] or 0
    
    return render(request, 'activity/activities/activityCompleted.html', {
        'score': score,
        'max_score': max_score,
        'show_score': show_score == 'True'
    })



class GradeEssayView(View):
    def get(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        student_questions = StudentQuestion.objects.filter(
            activity_question__activity=activity,
            activity_question__quiz_type__name='Essay',
            student_answer__isnull=False,
            status=False  # Only show ungraded essays
        )
        return render(request, 'activity/grade/gradeEssay.html', {
            'activity': activity,
            'student_questions': student_questions,
        })

    def post(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        student_questions = StudentQuestion.objects.filter(
            activity_question__activity=activity,
            activity_question__quiz_type__name='Essay',
            student_answer__isnull=False,
            status=False  # Only show ungraded essays
        )

        for student_question in student_questions:
            score = request.POST.get(f'score_{student_question.id}')
            max_score = student_question.activity_question.score 
            if score:
                score = float(score)
                if score > max_score:
                    return render(request, 'activity/grade/gradeEssay.html', {
                        'activity': activity,
                        'student_questions': student_questions,
                        'error': f"Score for {student_question.student.first_name} {student_question.student.last_name} cannot exceed {max_score}",
                    })
                student_question.score = score
                student_question.status = True 
                student_question.save()

        # Assuming you want to show the score and redirect correctly
        total_score = sum([student_question.score for student_question in student_questions])
        return redirect('activity_completed', score=int(total_score), activity_id=activity_id, show_score='true')



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
        max_score = ActivityQuestion.objects.filter(activity=activity).aggregate(Max('score'))['score__max']

        for student_activity in student_activities:
            section = Section.objects.filter(subjects=student_activity.activity.subject, assign_teacher=teacher).first()
            activity_detail = {
                'activity': student_activity.activity,
                'subject': student_activity.activity.subject.subject_name,
                'student': student_activity.student,
                'score': student_activity.score,
                'max_score': max_score,
                'section': section.section_name if section else 'N/A',  # Include section name
            }
            print(f"Activity Detail: {activity_detail}")
            activity_details.append(activity_detail)


    return render(request, 'activity/activities/allActivity.html', {'activity_details': activity_details})


class ActivityDetailView(View):
    def get(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        return render(request, 'activity/activityDetail.html', {
            'activity': activity
        })


def deleteActivityView(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    activity.delete()
    return redirect('courseList')