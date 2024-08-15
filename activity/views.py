from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import Activity, ActivityType, StudentActivity, ActivityQuestion, QuizType, QuestionChoice, StudentQuestion, get_upload_path  
from subject.models import Subject
from accounts.models import CustomUser
from course.models import Term, SubjectEnrollment
from django.db.models import Sum, Max
from django.utils import timezone
from django.core.files.storage import default_storage
from .forms import ActivityForm
import json 
import re

# Add type of activity
class AddActivityView(View):
    def get(self, request, subject_id):
        subject = get_object_or_404(Subject, id=subject_id)
        subject_enrollments = SubjectEnrollment.objects.filter(subject=subject)
        terms = Term.objects.filter(semester__in=[se.semester for se in subject_enrollments]).distinct()
        
        return render(request, 'activity/activities/createActivity.html', {
            'subject': subject,
            'activity_types': ActivityType.objects.all(),
            'terms': terms,
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

        students = CustomUser.objects.filter(subjectenrollment__subject=subject, profile__role__name__iexact='Student').distinct()
        for student in students:
            StudentActivity.objects.create(student=student, activity=activity, term=term)

        return redirect('add_quiz_type', activity_id=activity.id)


def UpdateActivity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)  
    if request.method == 'POST':  
        form = ActivityForm(request.POST, instance=activity)  
        if form.is_valid():  
            form.save()  
            return redirect('activity_detail', activity_id=activity.id)  
    else:
        form = ActivityForm(instance=activity)  
    return render(request, 'activity/activities/updateActivity.html', {'form': form, 'activity': activity}) 
    

# Add quiz type
class AddQuizTypeView(View):
    def get(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        quiz_types = QuizType.objects.all()  # Make sure "Document" is included here
        questions = request.session.get('questions', {}).get(str(activity_id), [])
        return render(request, 'activity/question/createQuizType.html', {
            'activity': activity,
            'quiz_types': quiz_types,
            'questions': questions
        })

    def post(self, request, activity_id):
        quiz_type_id = request.POST.get('quiz_type')
        return redirect('add_question', activity_id=activity_id, quiz_type_id=quiz_type_id)

# Add question to quiz
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

        # For Document type, handle file upload
        if quiz_type.name == 'Document':
            uploaded_file = request.FILES.get('document_file')
            if uploaded_file:
                file_path = default_storage.save(get_upload_path(None, uploaded_file.name), uploaded_file)
                correct_answer = file_path

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
    
# Delete temporary question
class DeleteTempQuestionView(View):
    def post(self, request, activity_id, index):
        questions = request.session.get('questions', {})
        activity_questions = questions.get(str(activity_id), [])
        
        if index < len(activity_questions):
            del activity_questions[index]
        
        questions[str(activity_id)] = activity_questions
        request.session['questions'] = questions
        
        return redirect('add_quiz_type', activity_id=activity_id)
    
# Save all created questions
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

            # Corrected query to fetch students enrolled in the subject
            students = CustomUser.objects.filter(
                profile__role__name__iexact='Student',
                subjectenrollment__subject=activity.subject
            ).distinct()
            
            for student in students:
                StudentQuestion.objects.create(student=student, activity_question=question)

        # Clear the questions from the session
        request.session.pop('questions', None)
        
        return redirect('SubjectList')
    
# Display questions the student will answer
class DisplayQuestionsView(View):
    def get(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        user = request.user
        questions = ActivityQuestion.objects.filter(activity=activity)

        # Check if the user is a teacher or a student
        is_teacher = user.is_authenticated and user.profile.role.name.lower() == 'teacher'
        is_student = user.is_authenticated and user.profile.role.name.lower() == 'student'

        # Prepare data for matching type questions (relevant for both students and teachers)
        for question in questions:
            if question.quiz_type.name == 'Matching':
                pairs = question.correct_answer.split(", ")
                question.pairs = []
                for pair in pairs:
                    if '->' in pair:
                        left, right = pair.split(" -> ")
                        question.pairs.append({"left": left, "right": right})

            # Handle Document type questions (teachers can see the document, students can upload)
            if question.quiz_type.name == 'Document':
                if is_teacher:
                    # Teacher will see the uploaded document link if available
                    question.document_link = question.correct_answer if question.correct_answer else None
                elif is_student:
                    # Student will see an option to upload a document
                    question.allow_upload = True

        context = {
            'activity': activity,
            'questions': questions,
            'is_teacher': is_teacher,
            'is_student': is_student,
        }

        return render(request, 'activity/question/displayQuestion.html', context)

# Submit answers
class SubmitAnswersView(View):
    def post(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        student = request.user
        total_score = 0
        has_non_essay_questions = False

        all_questions_answered = True  # Assume all questions are answered initially

        def normalize_text(text):
            """Normalize the text by removing non-alphanumeric characters and converting to lowercase."""
            return re.sub(r'\W+', '', text).lower()

        for question in ActivityQuestion.objects.filter(activity=activity):
            student_question, created = StudentQuestion.objects.get_or_create(student=student, activity_question=question)
            answer = request.POST.get(f'question_{question.id}')

            if question.quiz_type.name == 'Document':
                uploaded_file = request.FILES.get(f'question_{question.id}')
                if uploaded_file:
                    student_question.uploaded_file = uploaded_file
                    student_question.status = True
                else:
                    all_questions_answered = False
            elif question.quiz_type.name == 'Matching':
                matching_left = request.POST.getlist(f'matching_left_{question.id}')
                matching_right = request.POST.getlist(f'matching_right_{question.id}')
                if matching_left and matching_right:
                    student_answer = list(zip(matching_left, matching_right))
                    student_question.student_answer = str(student_answer)
                    student_question.status = True

                    # Normalize the student's answer
                    normalized_student_answer = [(normalize_text(left), normalize_text(right)) for left, right in student_answer]

                    # Manually compare the correct answer to the student's answer
                    correct_answer = question.correct_answer.split('->')
                    correct_answer_pairs = [(normalize_text(correct_answer[i]), normalize_text(correct_answer[i + 1]))
                                            for i in range(0, len(correct_answer), 2)]


                    if normalized_student_answer == correct_answer_pairs:
                        total_score += question.score
                        student_question.score = question.score
                else:
                    all_questions_answered = False
            else:
                if not answer and not student_question.student_answer:
                    all_questions_answered = False
                else:
                    student_question.student_answer = answer

                    if question.quiz_type.name == 'Essay':
                        student_question.status = True
                    else:
                        is_correct = (normalize_text(answer) == normalize_text(question.correct_answer))
                        if is_correct:
                            total_score += question.score
                            student_question.score = question.score
                        student_question.status = True
                        has_non_essay_questions = True
            
            student_question.submission_time = timezone.now()
            student_question.save()

        if all_questions_answered:
            student_activity, created = StudentActivity.objects.get_or_create(student=student, activity=activity)
            student_activity.save()

        return redirect('activity_completed', score=int(total_score), activity_id=activity_id, show_score=has_non_essay_questions)


# Display activity after activity is completed
def activityCompletedView(request, score, activity_id, show_score):
    activity = get_object_or_404(Activity, id=activity_id)
    max_score = activity.activityquestion_set.aggregate(total_score=Sum('score'))['total_score'] or 0
    
    contains_document = activity.activityquestion_set.filter(quiz_type__name='Document').exists()
    
    if contains_document:
        show_score = False
    else:
        show_score = show_score == 'True'
    
    return render(request, 'activity/activities/activityCompleted.html', {
        'score': score,
        'max_score': max_score,
        'show_score': show_score
    })

# Teacher grade essay
class GradeEssayView(View):
    def get(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        student_questions = StudentQuestion.objects.filter(
            activity_question__activity=activity,
            activity_question__quiz_type__name__in=['Essay', 'Document'],
            status=True, 
            score=0 
        )
        return render(request, 'activity/grade/gradeEssay.html', {
            'activity': activity,
            'student_questions': student_questions,
        })

    def post(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        student_questions = StudentQuestion.objects.filter(
            activity_question__activity=activity,
            activity_question__quiz_type__name__in=['Essay', 'Document'],
            status=True, 
            score=0 
        )

        total_score = 0

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
                total_score += score


        return redirect('grade_essay', activity_id=activity_id)

# Grade student individual essay
class GradeIndividualEssayView(View):
    def get(self, request, activity_id, student_question_id):
        activity = get_object_or_404(Activity, id=activity_id)
        student_question = get_object_or_404(StudentQuestion, id=student_question_id)

        return render(request, 'activity/grade/gradeIndividualEssay.html', {
            'activity': activity,
            'student_question': student_question,
        })

    def post(self, request, activity_id, student_question_id):
        activity = get_object_or_404(Activity, id=activity_id)
        student_question = get_object_or_404(StudentQuestion, id=student_question_id)

        score = request.POST.get('score')
        max_score = student_question.activity_question.score

        if score:
            score = float(score)
            if score > max_score:
                return render(request, 'activity/grade/gradeIndividualEssay.html', {
                    'activity': activity,
                    'student_question': student_question,
                    'error': f"Score cannot exceed {max_score}",
                })
            student_question.score = score
            student_question.status = True
            student_question.save()

        # Redirect to the subject detail page after grading
        return redirect('grade_essays', activity_id=activity_id)


# List all quizzes and exams for a teacher's students
def studentQuizzesExams(request):
    teacher = request.user

    # Get subjects where the teacher is assigned
    subjects = Subject.objects.filter(assign_teacher=teacher).distinct()

    # Get activities for these subjects
    activities = Activity.objects.filter(subject__in=subjects).distinct()

    activity_details = []

    student_activities = StudentActivity.objects.filter(activity__in=activities).select_related('student', 'activity', 'activity__subject')
    max_scores = ActivityQuestion.objects.filter(activity__in=activities).values('activity_id').annotate(Max('score'))

    max_score_dict = {item['activity_id']: item['score__max'] for item in max_scores}

    for student_activity in student_activities:
        activity_detail = {
            'activity': student_activity.activity,
            'subject': student_activity.activity.subject.subject_name,
            'student': student_activity.student,
            'score': student_activity.score,
            'max_score': max_score_dict.get(student_activity.activity_id, 0),
        }
        activity_details.append(activity_detail)

    return render(request, 'activity/activities/allActivity.html', {'activity_details': activity_details})

# Display activity details
class ActivityDetailView(View):
    def get(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        return render(request, 'activity/activities/activityDetail.html', {
            'activity': activity
        })

# Delete activity
def deleteActivityView(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    activity.delete()
    return redirect('subjectList')
