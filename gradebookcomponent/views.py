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
        
        for subject in subjects:
            if selected_subject_id != 'all' and str(subject.id) != selected_subject_id:
                continue

            student_scores_data = []
            term_has_data = False

            # Handle participation score separately
            participation_component = GradeBookComponents.objects.filter(
                teacher=user, subject=subject, is_participation=True
            ).first()

            if participation_component:
                for student in students:
                    if not student.subjectenrollment_set.filter(subject=subject).exists():
                        continue

                    participation_score = StudentParticipationScore.objects.filter(
                        student=student, subject=subject, term=term
                    ).first()

                    if participation_score:
                        weighted_participation_score = (participation_score.score / participation_score.max_score) * participation_component.percentage
                        term_has_data = True
                        print(f"Participation score found for student {student.get_full_name()} with score {participation_score.score}/{participation_score.max_score} in subject {subject.subject_name} for term {term.term_name}")

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

            # Handle other activity types
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
                    for student in students:
                        if not student.subjectenrollment_set.filter(subject=subject).exists():
                            continue

                        student_total_score = Decimal(0)
                        max_score_sum = Decimal(0)

                        student_questions = StudentQuestion.objects.filter(
                            student=student,
                            activity_question__activity=activity,
                            status=True 
                        )

                        if not student_questions.exists():
                            # If there are no student questions, mark the activity as missed
                            student_scores_data.append({
                                'student': student.get_full_name(),
                                'activity_name': activity.activity_name,
                                'question_text': 'No submission',
                                'score': 0,
                                'max_score': 0,  # Assuming max_score is unavailable if no questions are found
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
                            max_score = student_question.activity_question.score  # This is where you get the max score

                            # Convert score and max_score to Decimal before adding
                            student_total_score += Decimal(score)
                            max_score_sum += Decimal(max_score)
                            
                            print(f"Term: {term.term_name}, Student: {student.get_full_name()}, Question: {question}, Score: {score}/{max_score}")

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

    # Print participation data for each subject
    for term_data in term_scores_data:
        print(f"Participation scores for subject {term_data['subject'].subject_name}, term {term_data['term'].term_name}:")
        for data in term_data['student_scores_data']:
            if data['is_participation']:
                print(f"  Student: {data['student']}, Score: {data['total_score']}/{data['max_score']}, Weighted Score: {data['weighted_score']}")

    return render(request, 'gradebookcomponent/activityGrade/studentGrade.html', {
        'current_semester': current_semester,
        'terms': terms,
        'subjects': subjects,
        'term_scores_data': term_scores_data,
        'selected_term_id': selected_term_id,
        'selected_subject_id': selected_subject_id,
    })


def studentTotalScoreForActivityType(request):
    is_teacher = request.user.profile.role.name.lower() == 'teacher'
    students = CustomUser.objects.filter(profile__role__name__iexact='student')  
    return render(request, 'gradebookcomponent/activityGrade/studentTotalActivityScore.html', {
        'is_teacher': is_teacher,
        'students': students,  
    })


def studentTotalScoreApi(request):
    current_semester = get_current_semester()

    if not current_semester:
        return JsonResponse({'error': 'No current semester found.'}, status=400)

    user = request.user
    is_student = user.profile.role.name.lower() == 'student'

    if is_student:
        students = CustomUser.objects.filter(id=user.id)
        subjects = Subject.objects.filter(subjectenrollment__student=user)
        
        # Check if the student is allowed to view grades
        for subject in subjects:
            subject_enrollment = SubjectEnrollment.objects.get(student=user, subject=subject, semester=current_semester)
            if not subject_enrollment.can_view_grade:
                return JsonResponse({'message': 'Your grades are currently hidden by the teacher.'})

    else:
        students = CustomUser.objects.filter(profile__role__name__iexact='student')
        subjects = Subject.objects.filter(assign_teacher=user)
        
    activity_types = ActivityType.objects.all()
    terms = Term.objects.filter(semester=current_semester)

    selected_subject_id = request.GET.get('subject', 'all')

    if selected_subject_id != 'all':
        subjects = subjects.filter(id=selected_subject_id)

    student_data = defaultdict(lambda: defaultdict(list))
    student_total_weighted_grade = defaultdict(lambda: defaultdict(Decimal))

    for term in terms:
        for subject in subjects:
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
                teacher=user, subject=subject, is_participation=True
            ).first()

            if participation_component:
                for student in students:
                    if not student.subjectenrollment_set.filter(subject=subject).exists():
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

            for activity_type in activity_types:
                activities = Activity.objects.filter(term=term, activity_type=activity_type, subject=subject)

                try:
                    gradebook_component = GradeBookComponents.objects.get(
                        teacher=user,
                        subject=subject,
                        activity_type=activity_type
                    )
                    activity_percentage = Decimal(gradebook_component.percentage)
                except GradeBookComponents.DoesNotExist:
                    activity_percentage = Decimal(0)

                for student in students:
                    if not student.subjectenrollment_set.filter(subject=subject).exists():
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
                            # Mark missed activities
                            max_score = activity.activityquestion_set.aggregate(total_max_score=Sum('score'))['total_max_score'] or Decimal(0)
                            max_score_sum += Decimal(max_score)  # Ensure max_score is a Decimal
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
                    'missed': any(score.get('missed', False) for score in scores['term_scores'])  # Use get() to avoid KeyError
                })

    final_term_data = []
    for student_obj, subjects in student_data.items():
        student_subjects = []
        student_id = student_obj.id  # Access the student's ID from the object

        for subject_name, terms in subjects.items():
            subject_id = Subject.objects.get(subject_name=subject_name).id  # Retrieve the actual subject ID
            student_subjects.append({
                'subject_name': subject_name,
                'subject_id': subject_id,  # Include the subject ID in the response
                'terms': terms,
                'total_weighted_grade': float(student_total_weighted_grade[student_obj][subject_name])
            })
        final_term_data.append({
            'student': student_obj.get_full_name(),
            'student_id': student_id,
            'subjects': student_subjects
        })

    return JsonResponse({'term_data': final_term_data})




def getSubjects(request):
    current_semester = get_current_semester()

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


def studentSpecificGradeApi(request):
    current_semester = get_current_semester()

    if not current_semester:
        return JsonResponse({'error': 'No current semester found.'}, status=400)

    user = request.user
    is_student = user.profile.role.name.lower() == 'student'

    if not is_student:
        return JsonResponse({'error': 'Only students can access this data.'}, status=403)

    subjects = Subject.objects.filter(subjectenrollment__student=user)
    activity_types = ActivityType.objects.all()
    terms = Term.objects.filter(semester=current_semester)

    selected_subject_id = request.GET.get('subject', 'all')

    if selected_subject_id != 'all':
        subjects = subjects.filter(id=selected_subject_id)

    student_data = defaultdict(lambda: defaultdict(list))
    student_total_weighted_grade = defaultdict(lambda: defaultdict(Decimal))

    for term in terms:
        for subject in subjects:
            # Check if the student is allowed to view grades for this subject
            subject_enrollment = SubjectEnrollment.objects.get(student=user, subject=subject, semester=current_semester)
            if not subject_enrollment.can_view_grade:
                continue  # Skip this subject if grades are hidden

            student_scores = {'term_scores': [], 'total_weighted_score': Decimal(0)}

            try:
                term_gradebook_component = TermGradeBookComponents.objects.get(
                    term=term,
                    subjects=subject
                )
                term_percentage = Decimal(term_gradebook_component.percentage)
            except TermGradeBookComponents.DoesNotExist:
                term_percentage = Decimal(0)

            participation_component = GradeBookComponents.objects.filter(
                teacher=subject.assign_teacher, subject=subject, is_participation=True
            ).first()

            if participation_component:
                participation_score = StudentParticipationScore.objects.filter(
                    student=user, subject=subject, term=term
                ).first()

                if participation_score:
                    weighted_participation_score = (Decimal(participation_score.score) / Decimal(participation_score.max_score)) * Decimal(participation_component.percentage)
                    student_scores['term_scores'].append({
                        'term_name': term.term_name,
                        'activity_type': 'Participation',
                        'term_final_score': weighted_participation_score
                    })
                    student_scores['total_weighted_score'] += weighted_participation_score

            for activity_type in activity_types:
                activities = Activity.objects.filter(term=term, activity_type=activity_type, subject=subject)

                try:
                    gradebook_component = GradeBookComponents.objects.get(
                        teacher=subject.assign_teacher,
                        subject=subject,
                        activity_type=activity_type
                    )
                    activity_percentage = Decimal(gradebook_component.percentage)
                except GradeBookComponents.DoesNotExist:
                    activity_percentage = Decimal(0)

                student_total_score = Decimal(0)
                max_score_sum = Decimal(0)

                for activity in activities:
                    student_questions = StudentQuestion.objects.filter(
                        student=user,
                        activity_question__activity=activity,
                        status=True
                    )

                    if student_questions.exists():
                        for student_question in student_questions:
                            score = Decimal(student_question.score)
                            max_score = Decimal(student_question.activity_question.score)

                            student_total_score += score
                            max_score_sum += max_score
                    else:
                        # If the activity is missed, consider max score and set student score to 0
                        max_score = activity.activityquestion_set.aggregate(total_max_score=Sum('score'))['total_max_score'] or Decimal(0)
                        max_score_sum += Decimal(max_score)  # Explicitly convert to Decimal

                        student_scores['term_scores'].append({
                            'term_name': term.term_name,
                            'activity_type': activity_type.name,
                            'term_final_score': Decimal(0),
                            'missed': True
                        })

                if max_score_sum > 0:
                    weighted_score = (student_total_score / max_score_sum) * activity_percentage
                    student_scores['term_scores'].append({
                        'term_name': term.term_name,
                        'activity_type': activity_type.name,
                        'term_final_score': weighted_score
                    })
                    student_scores['total_weighted_score'] += weighted_score

            weighted_term_score = student_scores['total_weighted_score'] * (term_percentage / Decimal(100))
            student_total_weighted_grade[user.get_full_name()][subject.subject_name] += weighted_term_score

            max_possible_score = term_percentage
            weighted_term_percentage = (weighted_term_score / max_possible_score) * Decimal(100) if max_possible_score > 0 else Decimal(0)

            student_data[user.get_full_name()][subject.subject_name].append({
                'term_name': term.term_name,
                'total_weighted_score': f"{weighted_term_score:.6f}",
                'percentage': f"{weighted_term_percentage:.1f}%",
                'missed': any(score.get('missed', False) for score in student_scores['term_scores'])  # Track if any activities were missed
            })

    final_term_data = []
    for student, subjects in student_data.items():
        student_subjects = []
        for subject_name, terms in subjects.items():
            student_subjects.append({
                'subject_name': subject_name,
                'terms': terms,
                'total_weighted_grade': float(student_total_weighted_grade[student][subject_name])
            })
        final_term_data.append({
            'student': student,
            'subjects': student_subjects
        })

    return JsonResponse({'term_data': final_term_data})


def allowGradeVisibility(request, student_id):
    if request.method == "POST":
        subject_id = request.POST.get('subject_id')
        can_view_grade = request.POST.get('can_view_grade') == 'true'
        subject_enrollment = get_object_or_404(SubjectEnrollment, student_id=student_id, subject_id=subject_id)
        subject_enrollment.can_view_grade = can_view_grade
        subject_enrollment.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failure'}, status=400)