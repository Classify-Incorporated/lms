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
from random import shuffle
from datetime import timedelta
from django.core.mail import send_mass_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
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
            #created_by=request.user,
            start_date__lte=now,
            end_date__gte=now
        )
        

        students = CustomUser.objects.filter(subjectenrollment__subject=subject, subjectenrollment__semester=current_semester, subjectenrollment__status='enrolled',profile__role__name__iexact='Student').distinct()
        print('enrolled students', students)
        modules = Module.objects.filter(subject=subject, term__semester=current_semester, start_date__isnull=False, end_date__isnull=False) 

        activity_type_id = request.GET.get('activity_type_id', None)
        if activity_type_id:
            activity_type = get_object_or_404(ActivityType, id=activity_type_id)
        else:
            activity_type = None

        return render(request, 'activity/activities/createActivity.html', {
            'subject': subject,
            'activity_types': ActivityType.objects.all(),
            'terms': terms,
            'students': students,
            'modules': modules,
            'retake_methods': Activity.RETAKE_METHOD_CHOICES,
            'selected_activity_type': activity_type
        })

    def post(self, request, subject_id):
        print(request.POST)
        subject = get_object_or_404(Subject, id=subject_id)
        activity_name = request.POST.get('activity_name')
        activity_type_id = request.GET.get('activity_type_id') or request.POST.get('activity_type_id')
        term_id = request.POST.get('term')
        module_id = request.POST.get('module')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        try:
            max_retake = int(request.POST.get('max_retake', 2))  # Default to 2 if missing
            if max_retake < 0:  # Ensure it's not negative
                max_retake = 0
        except ValueError:
            max_retake = 2  # Number of retakes allowed
        retake_method = request.POST.get('retake_method', 'highest')
        remedial = request.POST.get('remedial') == 'on'  # Get remedial checkbox value
        remedial_students_ids = request.POST.getlist('remedial_students', None)  # Get selected students for remedial

        activity_type = get_object_or_404(ActivityType, id=activity_type_id)
        term = get_object_or_404(Term, id=term_id)
        module = get_object_or_404(Module, id=module_id)

        start_time = timezone.make_aware(timezone.datetime.strptime(start_time, '%Y-%m-%dT%H:%M'))
        end_time = timezone.make_aware(timezone.datetime.strptime(end_time, '%Y-%m-%dT%H:%M'))

        # Validation: Ensure that start_time is before end_time
        if start_time >= end_time:
            messages.error(request, 'End time must be after start time.')
            return self.get(request, subject_id)

        # Validation: Check if the activity name is unique for the semester and assigned teacher
        if Activity.objects.filter(activity_name=activity_name, term=term, subject=subject, subject__assign_teacher=subject.assign_teacher).exists():
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
            max_retake=max_retake,
            retake_method=retake_method,
            remedial=remedial
        )

        # print(f"Activity '{activity_name}' created for Subject: {subject.subject_name}, Term: {term.term_name}")

        if remedial and remedial_students_ids:
            # Add the remedial students to the activity (as multiple students can be added)
            remedial_students = CustomUser.objects.filter(id__in=remedial_students_ids)
            activity.remedial_students.set(remedial_students)
            for student in remedial_students:
                print(f"Remedial activity assigned to: {student.get_full_name()} (Student ID: {student.id}) - Status: Assigned to remedial activity")

        # Assign the activity to all students or specific remedial students
        if remedial and remedial_students_ids:
            for student_id in remedial_students_ids:
                student = CustomUser.objects.get(id=student_id)
                StudentActivity.objects.create(student=student, activity=activity, term=term)
            self.send_email_to_students(remedial_students, activity)
        else:
            students = CustomUser.objects.filter(subjectenrollment__subject=subject, subjectenrollment__semester=term.semester, subjectenrollment__status = 'enrolled', profile__role__name__iexact='Student').distinct()

            print(f"Students filtered for activity: {students}")
            for student in students:
                StudentActivity.objects.create(student=student, activity=activity, term=term)
                print(f"Activity assigned to: {student.get_full_name()} (Student ID: {student.id}) - Status: Assigned to regular activity")
            self.send_email_to_students(students, activity)

        return redirect('add_quiz_type', activity_id=activity.id)

    def send_email_to_students(self, students, activity):
        subject = f"New Activity Assigned: {activity.activity_name}"
        from_email = 'testsmtp@hccci.edu.ph' 

        email_messages = []
        print(f"Sending email for activity '{activity.activity_name}' to the following students:")
        
        base_url = 'http://localhost:8000/'  # Replace with your actual domain
        teacher_name = activity.subject.assign_teacher.get_full_name() if activity.subject.assign_teacher else 'Your Teacher'

        for student in students:
            student_email = student.email
            print(f"Preparing to send email to: {student.get_full_name()} - {student_email}")
            plain_message = f"""
            Dear {student.get_full_name()},
            
            A new activity has been assigned to you in the subject {activity.subject.subject_name}.
            
            Activity Name: {activity.activity_name}
            Start Time: {activity.start_time.strftime('%Y-%m-%d %H:%M')}
            End Time: {activity.end_time.strftime('%Y-%m-%d %H:%M')}
            
            Please log in to your account to complete the activity. Don't miss the deadline!

            You can view the activity here: {base_url}
            
            Best regards,
            {teacher_name}
            """
            
            # Add each email to the list of messages
            email_messages.append((subject, plain_message, from_email, [student_email]))

        # Bulk send the email messages
        try:
            send_mass_mail(email_messages, fail_silently=False)
            print("Emails successfully sent!")
        except Exception as e:
            print(f"Failed to send emails: {e}")

        print("Email sending process completed.")

# Update activity
@login_required
@permission_required('activity.change_activity', raise_exception=True)
def UpdateActivity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    subject = activity.subject

    if request.method == 'POST':
        form = ActivityForm(request.POST, request.FILES, instance=activity)
        remedial = request.POST.get('remedial') == 'on'  # Get remedial checkbox value
        remedial_students_ids = request.POST.getlist('remedial_students', None)  # Get selected students for remedial
        
        if form.is_valid():
            form.save()

            # Handle remedial students update
            if remedial and remedial_students_ids:
                remedial_students = CustomUser.objects.filter(id__in=remedial_students_ids)
                activity.remedial_students.set(remedial_students)
            else:
                # Clear remedial students if the remedial checkbox is not checked
                activity.remedial_students.clear()

            # Ensure the activity is updated for all students or specific remedial students
            if remedial and remedial_students_ids:
                for student_id in remedial_students_ids:
                    student = CustomUser.objects.get(id=student_id)
                    StudentActivity.objects.get_or_create(student=student, activity=activity, term=activity.term)
            else:
                students = CustomUser.objects.filter(subjectenrollment__subject=subject, profile__role__name__iexact='Student').distinct()
                for student in students:
                    StudentActivity.objects.get_or_create(student=student, activity=activity, term=activity.term)

            # Ensure StudentQuestion updates for each student and question in the activity
            if activity.term and activity.start_time and activity.end_time:
                students = CustomUser.objects.filter(subjectenrollment__subject=subject, profile__role__name__iexact='Student').distinct()
                for student in students:
                    student_activity, created = StudentActivity.objects.get_or_create(student=student, activity=activity)
                    for question in ActivityQuestion.objects.filter(activity=activity):
                        StudentQuestion.objects.get_or_create(
                            student=student,
                            activity_question=question,
                            activity=activity
                        )

            messages.success(request, 'Activity updated successfully!')
            return redirect('activityList', subject_id=subject.id)
        else:
            messages.error(request, 'There was an error updating the activity. Please try again.')
    else:
        form = ActivityForm(instance=activity)

    return render(request, 'activity/activities/updateActivity.html', {
        'form': form,
        'activity': activity,
        'modules': Module.objects.filter(subject=subject),
        'students': CustomUser.objects.filter(subjectenrollment__subject=subject, profile__role__name__iexact='Student').distinct(),
    })

# Add quiz type
@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('quiztype.add_quiztype', raise_exception=True), name='dispatch')
class AddQuizTypeView(View):
    def get(self, request, activity_id):
        try:
            print(f"Received activity_id: {activity_id}")
            activity = get_object_or_404(Activity, id=activity_id)
            quiz_types = QuizType.objects.all()  # Ensure that "Document" is included here

            is_participation = activity.activity_type.name == 'Participation'

            questions = request.session.get('questions', {}).get(str(activity_id), [])
            total_points = sum(question.get('score', 0) for question in questions)

            print(f"Activity ID: {activity_id}")
            print(f"Total Questions Retrieved: {len(questions)}")
            print(f"Total Points: {total_points}")

            return render(request, 'activity/question/createQuizType.html', {
                'activity': activity,
                'quiz_types': quiz_types,
                'questions': questions,
                'total_points': total_points,
                'is_participation': is_participation
            })
        
        except Exception as e:
            print(f"Error in AddQuizTypeView GET: {e}")
            messages.error(request, "An error occurred while loading the quiz types.")
            return redirect('error')  # Redirect to an error page

    def post(self, request, activity_id):
        try:
            activity = get_object_or_404(Activity, id=activity_id)
            quiz_type_id = request.POST.get('quiz_type')

            print(f"Quiz Type ID (POST): {quiz_type_id}")

            if not quiz_type_id or int(quiz_type_id) == 0:
                messages.error(request, "Quiz type not selected.")
                print("Error: Quiz type ID is zero or invalid.")
                return self.get(request, activity_id)
            else:
                print(f"Quiz type ID is valid and equals: {quiz_type_id}")

            return redirect('add_question', activity_id=activity_id, quiz_type_id=quiz_type_id)
        except Exception as e:
            print(f"Error in AddQuizTypeView POST: {e}")
            messages.error(request, "An error occurred while selecting the quiz type.")
            return redirect('error')

# Add question to quiz
@method_decorator(login_required, name='dispatch')
class AddQuestionView(View):
    def get(self, request, activity_id, quiz_type_id):
        try:
            activity = get_object_or_404(Activity, id=activity_id)
            quiz_type = get_object_or_404(QuizType, id=quiz_type_id)

            # If it's a participation quiz, fetch the related students
            if quiz_type.name == 'Participation':
                students = CustomUser.objects.filter(subjectenrollment__subject=activity.subject).distinct()
                return render(request, 'course/participation/addParticipation.html', {
                    'activity': activity,
                    'quiz_type': quiz_type,
                    'students': students
                })

            # Handle other quiz types
            return render(request, 'activity/question/createQuestion.html', {
                'activity': activity,
                'quiz_type': quiz_type,
            })

        except Exception as e:
            print(f"Error in AddQuestionView GET: {e}")
            messages.error(request, 'An error occurred while loading the question form.')
            return redirect('error')

    def post(self, request, activity_id, quiz_type_id):
        try:
            activity = get_object_or_404(Activity, id=activity_id)
            quiz_type = get_object_or_404(QuizType, id=quiz_type_id)

        except Activity.DoesNotExist:
            messages.error(request, 'Activity does not exist.')
            print(f"Activity with ID {activity_id} does not exist.")
            return redirect('error')  # Redirect to the correct error page
        except QuizType.DoesNotExist:
            messages.error(request, 'Quiz type does not exist.')
            print(f"QuizType with ID {quiz_type_id} does not exist.")
            return redirect('error')  # Redirect to the correct error page
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")
            print(f"Error in AddQuestionView GET method: {e}")
            return redirect('error')

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

        # Handle normal question submission for non-participation, non-MC types
        question_text = request.POST.get('question_text', '')
        correct_answer = ''
        score = float(request.POST.get('score', 0))

        # For Document type, handle file upload
        if quiz_type.name == 'Document':
            uploaded_file = request.FILES.get('document_file')
            if uploaded_file:
                file_path = default_storage.save(get_upload_path(None, uploaded_file.name), uploaded_file)
                correct_answer = file_path

        # Handle Multiple Choice, Matching, True/False
        choices = []
        if quiz_type.name == 'Multiple Choice':
            choices = request.POST.getlist('choices')
            correct_answer_index = int(request.POST.get('correct_answer'))
            if correct_answer_index < len(choices):
                correct_answer = choices[correct_answer_index]

        elif quiz_type.name == 'Matching':
            matching_left = request.POST.getlist('matching_left')
            matching_right = request.POST.getlist('matching_right')
            correct_answer = ", ".join([f"{left} -> {right}" for left, right in zip(matching_left, matching_right)])

        elif quiz_type.name in ['True/False', 'Calculated Numeric', 'Fill in the Blank']:
            correct_answer = request.POST.get('correct_answer', '')

        # Save the question in session
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
        activity = get_object_or_404(Activity, id=activity_id)
        if index >= len(questions):
            return redirect('add_quiz_type', activity_id=activity_id)  # Redirect if index is out of range

        question = questions[index]
        return render(request, 'activity/question/updateQuestion.html', {
            'activity_id': activity_id,
            'activity': activity,
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

        # Handle Multiple Choice (correct answer should be the index of the selected choice)
        if 'choices' in request.POST:
            question['choices'] = request.POST.getlist('choices')
            
            # Fetch the correct answer index from the form
            correct_answer_index = request.POST.get('correct_answer', None)
            if correct_answer_index is not None:
                correct_answer_index = int(correct_answer_index) + 1 
                if 0 <= correct_answer_index <= len(question['choices']):
                    question['correct_answer'] = correct_answer_index

        # For other types, handle correct answer normally
        elif question['quiz_type'] not in ['Essay', 'Document']:
            question['correct_answer'] = request.POST.get('correct_answer', '')

        # Update the specific question in the list
        questions[index] = question

        # Update the session
        request.session['questions'][str(activity_id)] = questions

        # Ensure the session is saved
        request.session.modified = True

        return redirect('add_quiz_type', activity_id=activity_id)

    
# Save all created questions
@method_decorator(login_required, name='dispatch')
class SaveAllQuestionsView(View):
    def post(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
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

                # Fetch students enrolled in the subject associated with the activity
                if activity.remedial:
                    # Fetch only the students assigned to the remedial activity
                    students = StudentActivity.objects.filter(activity=activity).values_list('student', flat=True)
                else:
                    # If not remedial, fetch all students enrolled in the subject
                    students = CustomUser.objects.filter(
                        profile__role__name__iexact='Student',
                        subjectenrollment__subject=activity.subject
                    ).distinct().values_list('id', flat=True)

                # Now assign the questions only to the filtered students
                for student_id in students:
                    student = CustomUser.objects.get(id=student_id)
                    StudentQuestion.objects.create(
                        student=student,
                        activity_question=question
                    )

        # Clear the questions from the session
        request.session.pop('questions', None)
        
        return redirect('subjectDetail', pk=activity.subject.id)
    
# Display questions the student will answer
@method_decorator(login_required, name='dispatch')
class DisplayQuestionsView(View):
    def get(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        user = request.user
        print(activity.max_retake)

        # Check if the user is a teacher or a student
        is_teacher = user.is_authenticated and user.profile.role.name.lower() == 'teacher'
        is_student = user.is_authenticated and user.profile.role.name.lower() == 'student'

        # If activity has ended, redirect based on role
        now = timezone.now()
        if activity.end_time and activity.end_time < now:
            if is_student:
                return redirect('studentActivityView', activity_id=activity.id)
            else:
                return redirect('teacherActivityView', activity_id=activity.id)

        # Retrieve or create student activity (only relevant for students)
        if is_student:
            student_activity, created = StudentActivity.objects.get_or_create(student=user, activity=activity)
            print(student_activity.retake_count)

            # If student has reached the maximum number of retakes, redirect
            if student_activity.retake_count > activity.max_retake:
                return redirect('studentActivityView', activity_id=activity.id)

            # Check if the student has already answered the questions
            student_questions = StudentQuestion.objects.filter(student=user, activity_question__activity=activity)
            has_answered = student_questions.filter(status=True).exists()

            # Start the timer only on the first attempt (if not answered yet)
            if not has_answered:
                if not student_activity.start_time:
                    student_activity.start_time = timezone.now()
                    student_activity.end_time = student_activity.start_time + timedelta(minutes=60)  # Set 1-hour time limit
                    student_activity.save()

            # If already answered, stop the timer (do not reset)
            if not created and has_answered:
                student_activity.start_time = None
                student_activity.end_time = None
                student_activity.save()

            # Calculate the remaining time for the student
            time_remaining = None
            if student_activity.end_time:
                time_remaining = student_activity.end_time - timezone.now()
                if time_remaining.total_seconds() <= 0:
                    # Time has run out, auto-submit any answers
                    return redirect('submit_answers', activity_id=activity_id)

            # Check if the student is allowed to retake
            can_retake = student_activity.retake_count <= activity.max_retake

        else:
            # For teachers, no timer or submission logic is needed
            student_activity = None
            has_answered = False
            time_remaining = None
            can_retake = False

        # Fetch activity questions
        questions = ActivityQuestion.objects.filter(activity=activity)

        # Prepare data for matching type questions (relevant for both students and teachers)
        for question in questions:
            if question.quiz_type.name == 'Matching':
                pairs = question.correct_answer.split(", ")
                question.pairs = []
                right_terms = []
                for pair in pairs:
                    if '->' in pair:
                        left, right = pair.split(" -> ")
                        question.pairs.append({"left": left, "right": right})
                        right_terms.append(right)

                shuffle(right_terms)
                question.shuffled_right_terms = right_terms

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
            'can_retake': can_retake,
            'has_answered': has_answered,
            'time_remaining': time_remaining.total_seconds() if time_remaining else None,
        }

        return render(request, 'activity/question/displayQuestion.html', context)

# Submit answers
@method_decorator(login_required, name='dispatch')
class SubmitAnswersView(View):
    def post(self, request, activity_id, auto_submit=False):
        activity = get_object_or_404(Activity, id=activity_id)
        student = request.user
        total_score_current_attempt = 0  # Track the total score for this attempt
        has_non_essay_questions = False

        

        student_activity, created = StudentActivity.objects.get_or_create(student=student, activity=activity)

        current_time = timezone.now()
        if current_time > student_activity.end_time:
            messages.error(request, 'Your time has expired. Your answers have been submitted automatically.')
            
        def normalize_text(text):
            """Normalize the text by removing non-alphanumeric characters and converting to lowercase."""
            return re.sub(r'\W+', '', text).lower()

    
        # Check if the student has exceeded the maximum number of retakes
        if student_activity.retake_count > activity.max_retake:
            messages.error(request, 'You have reached the maximum number of attempts for this activity.')
            return self.auto_submit_answers(student_activity)
        
        all_questions_answered = True  # Assume all questions are answered initially

        # Track the current attempt's scores for comparison
        current_attempt_scores = []

        # Loop through all questions in the activity
        for question in ActivityQuestion.objects.filter(activity=activity):
            student_question, created = StudentQuestion.objects.get_or_create(student=student, activity_question=question)
            answer = request.POST.get(f'question_{question.id}')
            current_score = 0  # Default score for the current question

            # Handle Document type
            if question.quiz_type.name == 'Document':
                uploaded_file = request.FILES.get(f'question_{question.id}')
                if uploaded_file:
                    student_question.uploaded_file = uploaded_file
                    student_question.student_answer = uploaded_file.name  # Store the file name as the answer
                    student_question.status = True
                else:
                    all_questions_answered = not auto_submit
                current_score = 0  # Documents are not auto-scored

            # Handle Matching type
            elif question.quiz_type.name == 'Matching':
                matching_left = []
                matching_right = []

                correct_answer_pairs = []
                correct_answer = question.correct_answer.split(", ")

                for pair in correct_answer:
                    if '->' in pair:
                        left, right = pair.split(" -> ")
                        correct_answer_pairs.append((normalize_text(left), normalize_text(right)))

                for idx in range(len(correct_answer_pairs)):
                    left = request.POST.get(f'matching_left_{question.id}_{idx}')
                    right = request.POST.get(f'matching_right_{question.id}_{idx}')

                    if left and right:
                        matching_left.append(left)
                        matching_right.append(right)

                if matching_left and matching_right and len(matching_left) == len(matching_right):
                    student_answer = list(zip(matching_left, matching_right))
                    student_question.student_answer = str(student_answer)
                    student_question.status = True
                    student_question.save()  # Explicit save for Matching answers

                    # Normalize the student's answer
                    normalized_student_answer = [(normalize_text(left), normalize_text(right)) for left, right in student_answer]

                    if normalized_student_answer == correct_answer_pairs:
                        current_score = question.score
                    else:
                        current_score = 0
                else:
                    all_questions_answered = not auto_submit
                    current_score = 0

            # Handle Essay type
            elif question.quiz_type.name == 'Essay':
                student_question.student_answer = answer
                student_question.status = True
                student_question.save()  # Explicitly save the essay answers
                current_score = 0  # Essays are not auto-scored

            # Handle other types like Multiple Choice, True/False, etc.
            else:
                if not answer and not student_question.student_answer:
                    all_questions_answered = not auto_submit
                    current_score = 0
                else:
                    student_question.student_answer = answer
                    if question.quiz_type.name != 'Essay':
                        is_correct = (normalize_text(answer) == normalize_text(question.correct_answer))
                        if is_correct:
                            current_score = question.score
                        else:
                            current_score = 0
                        student_question.status = True
                        has_non_essay_questions = True

            current_attempt_scores.append({
                'student_question': student_question,
                'current_score': current_score,
                'previous_score': student_question.score or 0
            })

            total_score_current_attempt += current_score  # Accumulate total score for this attempt
            student_question.submission_time = timezone.now()
            student_question.save()  # Save after processing each question

        # Calculate total score of all previous attempts
        previous_total_score = StudentQuestion.objects.filter(student=student, activity_question__activity=activity).aggregate(Sum('score'))['score__sum'] or 0

        # Compare total score of current attempt with previous attempts based on retake_method
        if activity.retake_method == 'highest':
            # If the current attempt's score is higher, save the new scores
            if total_score_current_attempt > previous_total_score:
                for score_data in current_attempt_scores:
                    score_data['student_question'].score = score_data['current_score']
                    score_data['student_question'].save()

        elif activity.retake_method == 'lowest':
            # If the current attempt's score is lower, save the new scores
            if total_score_current_attempt < previous_total_score:
                for score_data in current_attempt_scores:
                    score_data['student_question'].score = score_data['current_score']
                    score_data['student_question'].save()

        else:
            # If no retake method is set, always save the current attempt's score
            for score_data in current_attempt_scores:
                score_data['student_question'].score = score_data['current_score']
                score_data['student_question'].save()

        # Update student_activity with the current total score
        student_activity.total_score = StudentQuestion.objects.filter(student=student, activity_question__activity=activity).aggregate(Sum('score'))['score__sum'] or 0
        
        if student_activity.retake_count == activity.max_retake:
            student_activity.retake_count += 1
        student_activity.save()

        # Redirect based on whether all questions were answered
        if auto_submit or all_questions_answered:
            messages.success(request, 'Answers submitted successfully!')
            return redirect('activity_completed', score=int(total_score_current_attempt), activity_id=activity_id, show_score=has_non_essay_questions)
        else:
            messages.error(request, 'You did not answer all questions. Please complete the activity.')
            return redirect('display_question', activity_id=activity_id)
        
    def auto_submit_answers(self, student_activity):
        """
        Automatically submits answers if time expires.
        """
        student = student_activity.student
        activity = student_activity.activity

        # Fetch all questions for the activity
        questions = ActivityQuestion.objects.filter(activity=activity)

        # Initialize the total score for auto-submission
        total_score = 0

        for question in questions:
            # Check if the student has answered the question
            student_question, created = StudentQuestion.objects.get_or_create(student=student, activity_question=question)

            if not student_question.student_answer:
                # If the student hasn't answered the question, set the score to 0
                student_question.score = 0
                student_question.status = False  # Mark unanswered questions
            else:
                # Keep the existing score for the answered questions
                total_score += student_question.score or 0
                student_question.status = True

            student_question.submission_time = timezone.now()
            student_question.save()

        # Update the student's total score and retake count
        student_activity.total_score = total_score
        student_activity.retake_count += 1
        student_activity.save()

        # Redirect to the activity completion page
        return redirect('activity_completed', activity_id=activity.id)

        

@method_decorator(login_required, name='dispatch')
class RetakeActivityView(View):
    def post(self, request, activity_id):
        activity = get_object_or_404(Activity, id=activity_id)
        student = request.user

        # Get or create the student's activity record
        student_activity = StudentActivity.objects.get(student=student, activity=activity)

        # Check if the student can retake the activity
        if student_activity.retake_count < activity.max_retake:
            # Reset student questions and activity data for the retake
            StudentQuestion.objects.filter(student=student, activity_question__activity=activity).update(
                student_answer='',
                status=False,
                uploaded_file=None,
                score=0,  # Reset score as well if it exists
                submission_time=None  # Optionally reset submission time
            )

            student_activity.start_time = timezone.now()
            student_activity.retake_count += 1
            student_activity.end_time = student_activity.start_time + timedelta(minutes=1)
            student_activity.save()

            # Redirect back to the activity questions page for retaking
            return redirect('display_question', activity_id=activity_id)
        else:
            # If the student has reached the max retakes, show an error message
            messages.error(request, 'You have reached the maximum number of retakes for this activity.')
            return redirect('activity_detail', activity_id=activity_id)
    
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
    now = timezone.now()

    # Get the current semester based on the current date
    current_semester = Semester.objects.filter(start_date__lte=now, end_date__gte=now).first()

    # Get activities with a term that belongs to the current semester
    activities_with_term = Activity.objects.filter(subject=subject, term__semester=current_semester)

    # Get activities that do not have any term (copied activities)
    activities_without_term = Activity.objects.filter(subject=subject, term__isnull=True)

    # Combine both querysets into a list
    activities = list(activities_with_term) + list(activities_without_term)

    return render(request, 'activity/activities/activityList.html', {
        'subject': subject,
        'activities': activities,
        'current_semester': current_semester,  # Pass the current semester to the template (if needed)
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


@login_required
def participation_scores(request, activity_id):
    students = CustomUser.objects.filter(subjectenrollment__subject__activity=activity_id).distinct()
    student_data = [{'id': student.id, 'name': student.get_full_name()} for student in students]
    return JsonResponse({'students': student_data})