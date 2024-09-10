from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import Activity, ActivityType, StudentActivity, ActivityQuestion, QuizType, QuestionChoice, StudentQuestion, get_upload_path  
from subject.models import Subject
from accounts.models import CustomUser
from module.models import Module
from course.models import Term, Semester
from django.db.models import Sum, Max
from django.utils import timezone
from django.core.files.storage import default_storage
from .forms import ActivityForm, activityTypeForm
import re
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import permission_required
import csv
from io import TextIOWrapper
# Add type of activity

@login_required
def activityTypeList(request):
    activity_types = ActivityType.objects.all()
    form = activityTypeForm()  
    return render(request, 'activity/activityType/activityTypeList.html', {'activity_types': activity_types, 'form': form})

@login_required
def createActivityType(request):
    if request.method == 'POST':
        form = activityTypeForm(request.POST) 
        if form.is_valid(): 
            form.save() 
            messages.success(request, 'Activity type created successfully!')
            return redirect('activityTypeList')  
        else:
            messages.error(request, 'There was an error creating the activity type. Please try again.')
    else:
        form = activityTypeForm() 

    return render(request, 'activity/activityType/createActivityType.html', {'form': form})

@login_required
def updateActivityType(request, id):
    activityType = get_object_or_404(ActivityType, pk=id)
    if request.method == 'POST':
        form = activityTypeForm(request.POST, request.FILES, instance=activityType)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject updated successfully!')
            return redirect('subject')
        else:
            messages.error(request, 'There was an error updated the subject. Please try again.')
    else:
        form = activityTypeForm(instance=activityType)
    
    return render(request, 'activity/activityType/updateActivityType.html', {'form': form, 'activityType': activityType})


@login_required
def deleteActivityType(request, id):
    activity_type = get_object_or_404(ActivityType, id=id)
    activity_type.delete()
    messages.success(request, 'Activity type deleted successfully!')
    return redirect('activityTypeList')


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('activity.add_activity', raise_exception=True), name='dispatch')
class AddActivityView(View):
    def get(self, request, subject_id):
        subject = get_object_or_404(Subject, id=subject_id)

        now = timezone.localtime(timezone.now())
        current_semester = Semester.objects.filter(start_date__lte=now, end_date__gte=now).first()

        terms = Term.objects.filter(
            semester=current_semester,
            created_by=request.user,
            start_date__lte=now,
            end_date__gte=now
        )

        students = CustomUser.objects.filter(subjectenrollment__subject=subject, profile__role__name__iexact='Student').distinct()
        modules = Module.objects.filter(subject=subject) 

        return render(request, 'activity/activities/createActivity.html', {
            'subject': subject,
            'activity_types': ActivityType.objects.all(),
            'terms': terms,
            'students': students,
            'modules': modules,
        })

    def post(self, request, subject_id):
        subject = get_object_or_404(Subject, id=subject_id)
        activity_name = request.POST.get('activity_name')
        activity_type_id = request.POST.get('activity_type')
        term_id = request.POST.get('term')
        module_id = request.POST.get('module')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        remedial = request.POST.get('remedial') == 'on'  # Get remedial checkbox value
        remedial_students_ids = request.POST.getlist('remedial_students', None)  # Get selected students for remedial

        activity_type = get_object_or_404(ActivityType, id=activity_type_id)
        term = get_object_or_404(Term, id=term_id)
        module = get_object_or_404(Module, id=module_id)

        # Validation: Check if the activity name is unique for the semester and assigned teacher
        if Activity.objects.filter(activity_name=activity_name, term=term, subject__assign_teacher=subject.assign_teacher).exists():
            messages.error(request, 'An activity with this name already exists.')
            return self.get(request, subject_id)

        # Create the activity with the remedial option
        activity = Activity.objects.create(
            activity_name=activity_name,
            activity_type=activity_type,
            subject=subject,
            term=term,
            module=module,
            start_time=start_time,
            end_time=end_time,
            remedial=remedial
        )

        if remedial and remedial_students_ids:
            # Add the remedial students to the activity (as multiple students can be added)
            remedial_students = CustomUser.objects.filter(id__in=remedial_students_ids)
            activity.remedial_students.set(remedial_students)

        # Assign the activity to all students or specific remedial students
        if remedial and remedial_students_ids:
            for student_id in remedial_students_ids:
                student = CustomUser.objects.get(id=student_id)
                StudentActivity.objects.create(student=student, activity=activity, term=term)
        else:
            students = CustomUser.objects.filter(subjectenrollment__subject=subject, profile__role__name__iexact='Student').distinct()
            for student in students:
                StudentActivity.objects.create(student=student, activity=activity, term=term)

        return redirect('add_quiz_type', activity_id=activity.id)

# Update activity
@login_required
@permission_required('activity.change_activity', raise_exception=True)
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
@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('quiztype.add_quiztype', raise_exception=True), name='dispatch')
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
@method_decorator(login_required, name='dispatch')
class AddQuestionView(View):
    def get(self, request, activity_id, quiz_type_id):
        activity = get_object_or_404(Activity, id=activity_id)
        quiz_type = get_object_or_404(QuizType, id=quiz_type_id)

        if quiz_type.name == 'Participation':
            students = CustomUser.objects.filter(subjectenrollment__subject=activity.subject).distinct()
            return render(request, 'course/participation/addParticipation.html', {
                'activity': activity,
                'quiz_type': quiz_type,
                'students': students 
            })
        
        return render(request, 'activity/question/createQuestion.html', {
            'activity': activity,
            'quiz_type': quiz_type,
        })

    def post(self, request, activity_id, quiz_type_id):
        activity = get_object_or_404(Activity, id=activity_id)
        quiz_type = get_object_or_404(QuizType, id=quiz_type_id)

        # Handle participation quiz type
        if quiz_type.name == 'Participation':
            max_score = float(request.POST.get('max_score', 100))  
            students = CustomUser.objects.filter(subjectenrollment__subject=activity.subject).distinct()

            participation_data = []  

            for student in students:
                score = float(request.POST.get(f'score_{student.id}', 0))
                if score <= max_score:
                    participation_data.append({
                        'student_id': student.id,
                        'score': score
                    })
                else:
                    messages.error(request, f"Score for {student.get_full_name()} exceeds maximum score")
                    return self.get(request, activity_id, quiz_type_id)
                

        # Store the participation data in the session
            questions = request.session.get('questions', {})
            if str(activity_id) not in questions:
                questions[str(activity_id)] = []
            
            questions[str(activity_id)].append({
                'quiz_type': quiz_type.name,
                'participation_data': participation_data  # Store the participation data here
            })
            request.session['questions'] = questions
            request.session.modified = True
            return redirect('add_quiz_type', activity_id=activity.id)
        
        # Handle Multiple Choice CSV Import
        if quiz_type.name == 'Multiple Choice' and 'csv_file' in request.FILES:
            csv_file = request.FILES['csv_file']

            # Read and process the CSV file
            csv_data = TextIOWrapper(csv_file.file, encoding='utf-8')
            reader = csv.reader(csv_data)
            
            questions = request.session.get('questions', {})
            if str(activity_id) not in questions:
                questions[str(activity_id)] = []

            for row in reader:
                if len(row) >= 2:  # Assuming first column is question, remaining columns are choices
                    question_text = row[0]
                    points = float(row[1].strip().replace('"', ''))  # Strip quotes and convert to float
                    choices = [choice.strip().replace('"', '') for choice in row[2:-1]]  # Strip quotes from choices
                    correct_answer_text = row[-1].strip().replace('"', '')

                    # Assuming first choice is the correct answer
                    if correct_answer_text in choices:
                        correct_answer = correct_answer_text
                    else:
                        messages.error(request, f"Correct answer '{correct_answer_text}' not found in choices for question: {question_text}")
                        return redirect('add_quiz_type', activity_id=activity.id)


                    question = {
                        'question_text': question_text.strip().replace('"', ''),
                        'correct_answer': correct_answer,
                        'quiz_type': quiz_type.name,
                        'score': points,  # Default score for each question
                        'choices': choices
                    }
                    questions[str(activity_id)].append(question)

            # Save questions in session
            request.session['questions'] = questions
            request.session.modified = True
            return redirect('add_quiz_type', activity_id=activity.id)

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
@method_decorator(login_required, name='dispatch')
class DeleteTempQuestionView(View):
    def post(self, request, activity_id, index):
        questions = request.session.get('questions', {})
        activity_questions = questions.get(str(activity_id), [])
        
        if index < len(activity_questions):
            del activity_questions[index]
        
        questions[str(activity_id)] = activity_questions
        request.session['questions'] = questions
        
        return redirect('add_quiz_type', activity_id=activity_id)\

# edit temporary question
@method_decorator(login_required, name='dispatch')
class UpdateQuestionView(View):
    def get(self, request, activity_id, index):
        questions = request.session.get('questions', {}).get(str(activity_id), [])
        if index >= len(questions):
            return redirect('add_quiz_type', activity_id=activity_id)  # Redirect if index is out of range

        question = questions[index]
        return render(request, 'activity/question/updateQuestion.html', {
            'activity_id': activity_id,
            'index': index,
            'question': question,
        })

    def post(self, request, activity_id, index):
        questions = request.session.get('questions', {}).get(str(activity_id), [])
        if index >= len(questions):
            return redirect('add_quiz_type', activity_id=activity_id)  # Redirect if index is out of range

        question = questions[index]
        question['question_text'] = request.POST.get('question_text', '')
        question['score'] = float(request.POST.get('score', 0))
        question['correct_answer'] = request.POST.get('correct_answer', '')

        if 'choices' in request.POST:
            question['choices'] = request.POST.getlist('choices')

        # Update the specific question in the list
        questions[index] = question  
        
        # Update the session
        request.session['questions'][str(activity_id)] = questions
        
        # Force save the session to ensure it's persisted
        request.session.modified = True

        return redirect('add_quiz_type', activity_id=activity_id)
    
# Save all created questions
@method_decorator(login_required, name='dispatch')
class SaveAllQuestionsView(View):
    def post(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        print(f"Activity ID: {activity_id}, Found Activity: {activity.activity_name}")
        questions = request.session.get('questions', {}).get(str(activity_id), [])

        
        for i, question_data in enumerate(questions):
            quiz_type = get_object_or_404(QuizType, name=question_data['quiz_type'])

            if quiz_type.name == 'Participation':
                participation_data = question_data.get('participation_data', [])
                for participation in participation_data:
                    student = CustomUser.objects.get(id=participation['student_id'])
                    StudentQuestion.objects.create(
                        student=student,
                        activity=activity,  # Link to the activity
                        activity_question=None,  # No need to link to ActivityQuestion for Participation
                        score=participation['score'],
                        student_answer=None,
                        uploaded_file=None,
                        is_participation=True
                    )
                print(f"Saved participation data for Activity: {activity.activity_name}")
            else:
                question = ActivityQuestion.objects.create(
                    activity=activity,
                    question_text=question_data['question_text'],
                    correct_answer=question_data['correct_answer'],
                    quiz_type=quiz_type,
                    score=question_data['score']
                )

                if quiz_type.name == 'Multiple Choice':
                    for choice_text in question_data['choices']:
                        choice = QuestionChoice.objects.create(question=question, choice_text=choice_text)
                        print(f"Saved choice for Question {i}: {choice_text}")

                # Fetch students enrolled in the subject associated with the activity
                if activity.remedial:
                    # Fetch only the students assigned to the remedial activity
                    students = StudentActivity.objects.filter(activity=activity).values_list('student', flat=True)
                    print(f"Creating questions for remedial students only: {students}")
                else:
                    # If not remedial, fetch all students enrolled in the subject
                    students = CustomUser.objects.filter(
                        profile__role__name__iexact='Student',
                        subjectenrollment__subject=activity.subject
                    ).distinct().values_list('id', flat=True)
                    print(f"Creating questions for all students: {students}")

                # Now assign the questions only to the filtered students
                for student_id in students:
                    student = CustomUser.objects.get(id=student_id)
                    StudentQuestion.objects.create(
                        student=student,
                        activity_question=question
                    )
                    print(f"Created StudentQuestion for {student.get_full_name()}")

        # Clear the questions from the session
        request.session.pop('questions', None)
        
        return redirect('subjectDetail', pk=activity.subject.id)
    
# Display questions the student will answer
@method_decorator(login_required, name='dispatch')
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
@method_decorator(login_required, name='dispatch')
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
@login_required
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
@method_decorator(login_required, name='dispatch')
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

        messages.success(request, 'Activity successfully graded.')
        return redirect('grade_essay', activity_id=activity_id)

# Grade student individual essay
@method_decorator(login_required, name='dispatch')
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

@login_required
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
@method_decorator(login_required, name='dispatch')
class ActivityDetailView(View):
    def get(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        return render(request, 'activity/activities/activityDetail.html', {
            'activity': activity
        })

# Delete activity
@login_required
def deleteActivityView(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    activity.delete()
    return redirect('subjectList')

@login_required
def activityList(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    activities = Activity.objects.filter(subject=subject)

    return render(request, 'activity/activities/activityList.html', {
        'subject': subject,
        'activities': activities,
    })

@login_required
@require_POST
def toggleShowScore(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    activity.show_score = not activity.show_score
    activity.save()
    return JsonResponse({'success': True, 'show_score': activity.show_score})

@login_required
def deleteActivity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    subject_id = activity.subject.id 
    activity.delete() 
    messages.success(request, 'Activity deleted successfully!')
    return redirect('activityList', subject_id=subject_id)