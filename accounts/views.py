from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as auth_logout, authenticate, login
from .forms import CustomLoginForm, profileForm
from .models import Profile
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.contrib.auth import get_user_model
from course.models import Semester, SubjectEnrollment
from subject.models import Subject
from django.db.models import Count, Prefetch
from datetime import timedelta
import requests
from bs4 import BeautifulSoup
import requests
import os
from .models import CustomUser
from decimal import Decimal
from collections import defaultdict
from gradebookcomponent.models import GradeBookComponents, TermGradeBookComponents
from course.models import Term,  StudentParticipationScore
from activity.models import Activity, ActivityType, StudentQuestion
from django.db.models import Sum
from django.contrib.auth.decorators import permission_required
from datetime import datetime
from django.core.cache import cache

def admin_login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                return render(request, 'accounts/login.html', {'form': form, 'error': 'Invalid email or password'})
        else:
            return render(request, 'accounts/login.html', {'form': form, 'error': 'Form data is not valid'})
    else:
        form = CustomLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
@permission_required('accounts.view_profile', raise_exception=True)
def student(request):
    profiles = Profile.objects.filter(role__name__iexact='student')
    return render(request, 'accounts/student.html', {'profiles': profiles})

@login_required
@permission_required('accounts.view_profile', raise_exception=True)
def staff_list(request):
    staff = Profile.objects.exclude(role__name__iexact='student').exclude(role__name__iexact='admin')
    return render(request, 'accounts/staffList.html', {'staff': staff})

@login_required
@permission_required('accounts.view_profile', raise_exception=True)
def viewProfile(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    return render(request, 'accounts/viewStudentProfile.html',{'profile': profile})

@login_required
@permission_required('accounts.change_profile', raise_exception=True)
def updateProfile(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    if request.method == 'POST':
        form = profileForm(request.POST,request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('staff_list')
    else:
        form = profileForm(instance=profile)
    return render(request, 'accounts/updateStudentProfile.html', {'form': form,'profile': profile})


@login_required
@permission_required('accounts.delete_profile', raise_exception=True)
def activateProfile(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    profile.active = True
    profile.save()
    return redirect('viewProfile', pk=profile.pk)

@login_required
@permission_required('accounts.delete_profile', raise_exception=True)
def deactivateProfile(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    profile.active = False
    profile.save()
    return redirect('viewProfile', pk=profile.pk)


def fetch_facebook_posts():
    # Try to cache the Facebook posts for some time (e.g., 10 minutes) to reduce repeated API calls
    cache_key = 'facebook_posts'
    cached_posts = cache.get(cache_key)
    if cached_posts:
        return cached_posts

    page_id = '370354416168614'
    access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
    url = f"https://graph.facebook.com/v20.0/{page_id}/posts"
    params = {
        'access_token': access_token,
        'fields': 'message,created_time,from{id,name},permalink_url,attachments{media}'
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        posts = response.json().get('data', [])
        processed_posts = []
        for post in posts:
            attachments = post.get('attachments', {}).get('data', [])
            image_url = None
            if attachments:
                for attachment in attachments:
                    if 'media' in attachment and 'image' in attachment['media']:
                        image_url = attachment['media']['image']['src']
                        break

            message = post.get('message', '')
            first_paragraph = message.split('\n')[0] if message else 'No subject available'

            posted_by = post.get('from', {}).get('name', 'Unknown')
            posted_by_id = post.get('from', {}).get('id')

            # Fetch profile picture
            profile_picture_url = None
            if posted_by_id:
                profile_picture_response = requests.get(
                    f"https://graph.facebook.com/v20.0/{posted_by_id}/picture?type=small&redirect=false",
                    params={'access_token': access_token}
                )
                if profile_picture_response.status_code == 200:
                    profile_picture_data = profile_picture_response.json()
                    profile_picture_url = profile_picture_data.get('data', {}).get('url')

            processed_posts.append({
                'message': first_paragraph,
                'created_time': post.get('created_time', ''),
                'posted_by': posted_by,
                'profile_picture_url': profile_picture_url,
                'permalink_url': post.get('permalink_url', ''),
                'image_url': image_url,
            })

        # Cache the result for 10 minutes
        cache.set(cache_key, processed_posts, timeout=600)
        return processed_posts
    else:
        return []

@login_required
@login_required
def dashboard(request):
    # Get the current time and greeting based on the hour
    current_hour = datetime.now().hour
    greeting = "Good Morning" if current_hour < 12 else ("Good Afternoon" if current_hour < 18 else "Good Evening")

    # Cache active students and other counts (optional, based on frequency of changes)
    cache_key_students = f'active_students_{request.user.id}'
    active_students_count = cache.get(cache_key_students)
    if not active_students_count:
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        user_ids = [session.get_decoded().get('_auth_user_id') for session in sessions]
        active_students_count = get_user_model().objects.filter(
            id__in=user_ids,
            profile__role__name__iexact='student'
        ).distinct().count()
        cache.set(cache_key_students, active_students_count, timeout=300)  # Cache for 5 minutes

    # Cache subjects and related counts
    today = timezone.now().date()
    current_semester = Semester.objects.filter(start_date__lte=today, end_date__gte=today).first()

    if current_semester:
        user = request.user
        role_name = getattr(user.profile.role, 'name', '').lower() if hasattr(user, 'profile') else None
        is_teacher = role_name == 'teacher'
        is_student = role_name == 'student'

        # Optimize subject and student queries
        if is_teacher:
            subjects = Subject.objects.filter(
                assign_teacher=user,
                subjectenrollment__semester=current_semester
            ).distinct().prefetch_related(Prefetch('subjectenrollment_set'))
        elif is_student:
            subjects = Subject.objects.filter(
                subjectenrollment__student=user,
                subjectenrollment__semester=current_semester
            ).distinct().prefetch_related(Prefetch('subjectenrollment_set'))
        else:
            subjects = Subject.objects.filter(
                subjectenrollment__semester=current_semester
            ).distinct().prefetch_related(Prefetch('subjectenrollment_set'))

        subject_count = subjects.count()

        # Efficiently calculate student count per subject using annotate
        student_counts = subjects.annotate(student_count=Count('subjectenrollment')).order_by('-student_count')

        # Cache expensive computations like failing and excelling students
        cache_key_failing = f'failing_students_{current_semester.id}_{request.user.id}'
        failing_students_count = cache.get(cache_key_failing)
        if not failing_students_count:
            failing_students_count = get_failing_students_count(current_semester, request.user)
            cache.set(cache_key_failing, failing_students_count, timeout=300)  # Cache for 5 minutes

        cache_key_excelling = f'excelling_students_{current_semester.id}_{request.user.id}'
        excelling_students_count = cache.get(cache_key_excelling)
        if not excelling_students_count:
            excelling_students_count = get_excelling_students_count(current_semester, request.user)
            cache.set(cache_key_excelling, excelling_students_count, timeout=300)  # Cache for 5 minutes
    else:
        subject_count = 0
        student_counts = []
        failing_students_count = 0
        excelling_students_count = 0

    # Fetch and cache Facebook posts
    articles = fetch_facebook_posts()

    context = {
        'active_users_count': active_students_count,
        'student_counts': student_counts,
        'subject_count': subject_count,
        'failing_students_count': failing_students_count,
        'excelling_students_count': excelling_students_count,
        'current_semester': current_semester,
        'articles': articles,
        'greeting': greeting,
        'user_name': user.first_name or user.username,  # Use the first name or username
    }

    return render(request, 'accounts/dashboard.html', context)



def get_failing_students_count(current_semester, user):
    FAILING_THRESHOLD = Decimal(65)

    # Determine the user's role
    is_teacher = user.profile.role.name.lower() == 'teacher'
    is_student = user.profile.role.name.lower() == 'student'

    # If the user is an admin (not a teacher or student), get all students and subjects
    if is_teacher:
        students = CustomUser.objects.filter(profile__role__name__iexact='student')
        subjects = Subject.objects.filter(assign_teacher=user, subjectenrollment__semester=current_semester).distinct()
    elif is_student:
        students = CustomUser.objects.filter(id=user.id)
        subjects = Subject.objects.filter(subjectenrollment__student=user, subjectenrollment__semester=current_semester).distinct()
    else:
        # Admin or other non-teaching, non-student roles: fetch all students and subjects
        students = CustomUser.objects.filter(profile__role__name__iexact='student')
        subjects = Subject.objects.filter(subjectenrollment__semester=current_semester).distinct()

    failing_students_set = set()  # To store unique student IDs

    for term in Term.objects.filter(semester=current_semester):
        for subject in subjects:
            for student in students:
                subject_enrollment = SubjectEnrollment.objects.filter(student=student, subject=subject, semester=current_semester).first()
                if not subject_enrollment or not subject_enrollment.can_view_grade:
                    continue

                student_scores = defaultdict(lambda: {'total_weighted_score': Decimal(0)})

                # Calculate participation score
                participation_component = GradeBookComponents.objects.filter(
                    teacher=user if is_teacher else subject.assign_teacher,
                    subject=subject,
                    is_participation=True
                ).first()

                if participation_component:
                    participation_score = StudentParticipationScore.objects.filter(
                        student=student, subject=subject, term=term
                    ).first()

                    if participation_score:
                        weighted_participation_score = (Decimal(participation_score.score) / Decimal(participation_score.max_score)) * Decimal(participation_component.percentage)
                        student_scores[student]['total_weighted_score'] += weighted_participation_score

                # Calculate activity scores
                for activity_type in ActivityType.objects.all():
                    activities = Activity.objects.filter(term=term, activity_type=activity_type, subject=subject)

                    gradebook_component = GradeBookComponents.objects.filter(
                        teacher=user if is_teacher else subject.assign_teacher,
                        subject=subject,
                        activity_type=activity_type
                    ).first()

                    if not gradebook_component:
                        continue

                    activity_percentage = Decimal(gradebook_component.percentage)
                    student_total_score = Decimal(0)
                    max_score_sum = Decimal(0)

                    for activity in activities:
                        student_questions = StudentQuestion.objects.filter(
                            student=student,
                            activity_question__activity=activity,
                            status=True
                        )

                        if not student_questions.exists():
                            max_score_sum += Decimal(activity.activityquestion_set.aggregate(total_max_score=Sum('score'))['total_max_score'] or Decimal(0))
                            continue

                        for student_question in student_questions:
                            score = Decimal(student_question.score)
                            max_score = Decimal(student_question.activity_question.score)

                            student_total_score += score
                            max_score_sum += max_score

                    if max_score_sum > 0:
                        weighted_score = (student_total_score / max_score_sum) * activity_percentage
                        student_scores[student]['total_weighted_score'] += weighted_score

                # Calculate the final weighted score considering the term percentage
                try:
                    term_gradebook_component = TermGradeBookComponents.objects.get(
                        term=term,
                        subjects=subject
                    )
                    term_percentage = Decimal(term_gradebook_component.percentage)
                except TermGradeBookComponents.DoesNotExist:
                    term_percentage = Decimal(0)

                weighted_term_score = student_scores[student]['total_weighted_score'] * (term_percentage / Decimal(100))

                # Convert the weighted term score to a percentage
                percentage_score = (weighted_term_score / term_percentage) * Decimal(100) if term_percentage > 0 else Decimal(0)

                # Add to the set if below the failing threshold
                if percentage_score < FAILING_THRESHOLD:
                    failing_students_set.add(student.id)

    return len(failing_students_set)

def get_excelling_students_count(current_semester, user):
    EXCELLING_THRESHOLD = Decimal(80)

    # Determine the user's role
    is_teacher = user.profile.role.name.lower() == 'teacher'
    is_student = user.profile.role.name.lower() == 'student'

    # If the user is an admin (not a teacher or student), get all students and subjects
    if is_teacher:
        students = CustomUser.objects.filter(profile__role__name__iexact='student')
        subjects = Subject.objects.filter(assign_teacher=user, subjectenrollment__semester=current_semester).distinct()
    elif is_student:
        students = CustomUser.objects.filter(id=user.id)
        subjects = Subject.objects.filter(subjectenrollment__student=user, subjectenrollment__semester=current_semester).distinct()
    else:
        # Admin or other non-teaching, non-student roles: fetch all students and subjects
        students = CustomUser.objects.filter(profile__role__name__iexact='student')
        subjects = Subject.objects.filter(subjectenrollment__semester=current_semester).distinct()

    excelling_students_set = set()  # To store unique student IDs

    for term in Term.objects.filter(semester=current_semester):
        for subject in subjects:
            for student in students:
                subject_enrollment = SubjectEnrollment.objects.filter(student=student, subject=subject, semester=current_semester).first()
                if not subject_enrollment or not subject_enrollment.can_view_grade:
                    continue

                student_scores = defaultdict(lambda: {'total_weighted_score': Decimal(0)})

                # Calculate participation score
                participation_component = GradeBookComponents.objects.filter(
                    teacher=user if is_teacher else subject.assign_teacher,
                    subject=subject,
                    is_participation=True
                ).first()

                if participation_component:
                    participation_score = StudentParticipationScore.objects.filter(
                        student=student, subject=subject, term=term
                    ).first()

                    if participation_score:
                        weighted_participation_score = (Decimal(participation_score.score) / Decimal(participation_score.max_score)) * Decimal(participation_component.percentage)
                        student_scores[student]['total_weighted_score'] += weighted_participation_score

                # Calculate activity scores
                for activity_type in ActivityType.objects.all():
                    activities = Activity.objects.filter(term=term, activity_type=activity_type, subject=subject)

                    gradebook_component = GradeBookComponents.objects.filter(
                        teacher=user if is_teacher else subject.assign_teacher,
                        subject=subject,
                        activity_type=activity_type
                    ).first()

                    if not gradebook_component:
                        continue

                    activity_percentage = Decimal(gradebook_component.percentage)
                    student_total_score = Decimal(0)
                    max_score_sum = Decimal(0)

                    for activity in activities:
                        student_questions = StudentQuestion.objects.filter(
                            student=student,
                            activity_question__activity=activity,
                            status=True
                        )

                        if not student_questions.exists():
                            max_score_sum += Decimal(activity.activityquestion_set.aggregate(total_max_score=Sum('score'))['total_max_score'] or Decimal(0))
                            continue

                        for student_question in student_questions:
                            score = Decimal(student_question.score)
                            max_score = Decimal(student_question.activity_question.score)

                            student_total_score += score
                            max_score_sum += max_score

                    if max_score_sum > 0:
                        weighted_score = (student_total_score / max_score_sum) * activity_percentage
                        student_scores[student]['total_weighted_score'] += weighted_score

                # Calculate the final weighted score considering the term percentage
                try:
                    term_gradebook_component = TermGradeBookComponents.objects.get(
                        term=term,
                        subjects=subject
                    )
                    term_percentage = Decimal(term_gradebook_component.percentage)
                except TermGradeBookComponents.DoesNotExist:
                    term_percentage = Decimal(0)

                weighted_term_score = student_scores[student]['total_weighted_score'] * (term_percentage / Decimal(100))

                # Convert the weighted term score to a percentage
                percentage_score = (weighted_term_score / term_percentage) * Decimal(100) if term_percentage > 0 else Decimal(0)

                # Add to the set if above excelling threshold
                if percentage_score >= EXCELLING_THRESHOLD:
                    excelling_students_set.add(student.id)

    return len(excelling_students_set)


def activity_stream(request):
    return render(request, 'accounts/activity_stream.html')

def assist(request):
    return render(request, 'accounts/assist.html')

def tools(request):
    return render(request, 'accounts/tools.html')

def createProfile(request):
    return render(request, 'accounts/createStudentProfile.html')

def error(request):
    return render(request, '404.html')

def sign_out(request):
    auth_logout(request)
    return redirect('admin_login_view')
