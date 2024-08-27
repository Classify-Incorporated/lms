from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as auth_logout, authenticate, login
from .forms import CustomLoginForm, profileForm
from .models import CustomUser, Profile
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.contrib.auth import get_user_model
from course.models import Semester, SubjectEnrollment
from subject.models import Subject
from django.db.models import Count
from datetime import timedelta
import requests
from bs4 import BeautifulSoup
import requests
from django.conf import settings
from django.http import JsonResponse

@login_required
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
def student(request):
    profiles = Profile.objects.filter(role__name__iexact='student')
    return render(request, 'accounts/student.html', {'profiles': profiles})

@login_required
def staff_list(request):
    staff = Profile.objects.exclude(role__name__iexact='student').exclude(role__name__iexact='admin')
    return render(request, 'accounts/staffList.html', {'staff': staff})

@login_required
def viewProfile(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    return render(request, 'accounts/viewStudentProfile.html',{'profile': profile})

@login_required
def updateProfile(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    if request.method == 'POST':
        form = profileForm(request.POST,request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('student')
    else:
        form = profileForm(instance=profile)
    return render(request, 'accounts/updateStudentProfile.html', {'form': form,'profile': profile})

@login_required
def activateProfile(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    profile.active = True
    profile.save()
    return redirect('viewProfile', pk=profile.pk)

@login_required
def deactivateProfile(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    profile.active = False
    profile.save()
    return redirect('viewProfile', pk=profile.pk)

def fetch_lms_articles():
    url = "https://www.techlearning.com/news"  # Example URL
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    articles = []
    for item in soup.select('.listingResult.small'):
        title_element = item.select_one('h3')
        description_element = item.select_one('p')
        link_element = item.select_one('a')
        thumbnail_element = item.select_one('img')

        if title_element and description_element and link_element:
            title = title_element.get_text(strip=True)
            description = description_element.get_text(strip=True)
            link = link_element['href']
            thumbnail = thumbnail_element['src'] if thumbnail_element else 'default_thumbnail.jpg'

            articles.append({
                'title': title,
                'description': description,
                'url': link,
                'thumbnail_url': thumbnail,
            })

    return articles



def fetch_facebook_posts(request):
    page_id = '370354416168614'
    access_token = 'EAAWtZAc96AJsBO5lhwJDiIuGxqWEGpnYnEopQuITyNrKfbPvA9aXKt7MoWd6wHW7lJm95cZAdgBLDRXqMuazx9FPNOxGZC7XUP2moKTTLripZB0PqgH1r6AFv5ZBIaxN0md5YV1xVRO06wXQ7Cu8ZBPCC0s9EdCmht1A5To7cl0zOtekGHbZAlzj8sm8UoTIt9ZCy4b7nEXQZAwaOwNYaxrIZCtBeu7LIKHAl3'
    url = f"https://graph.facebook.com/v20.0/{page_id}/posts"
    params = {
        'access_token': access_token,
        'fields': 'message,created_time,id,permalink_url,attachments{media}'
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        posts = response.json().get('data', [])
        # Process the posts to include only the necessary fields
        processed_posts = []
        for post in posts:
            attachments = post.get('attachments', {}).get('data', [])
            image_url = None
            if attachments:
                for attachment in attachments:
                    if 'media' in attachment and 'image' in attachment['media']:
                        image_url = attachment['media']['image']['src']
                        break  # We found the image, no need to look further

            processed_posts.append({
                'message': post.get('message', ''),
                'created_time': post.get('created_time', ''),
                'permalink_url': post.get('permalink_url', ''),
                'image_url': image_url,
            })
        return processed_posts
    else:
        return []


def dashboard(request):
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    user_ids = []

    for session in sessions:
        session_data = session.get_decoded()
        user_id = session_data.get('_auth_user_id')
        if user_id:
            user_ids.append(user_id)

    active_users = get_user_model().objects.filter(id__in=user_ids).distinct()
    active_users_count = active_users.count()

    today = timezone.now().date()
    current_semester = Semester.objects.filter(start_date__lte=today, end_date__gte=today).first()

    if current_semester:
        subject_count = Subject.objects.filter(subjectenrollment__semester=current_semester).distinct().count()
        student_counts = SubjectEnrollment.objects.filter(semester=current_semester) \
                                                  .values('subject__subject_name') \
                                                  .annotate(student_count=Count('student')) \
                                                  .order_by('-student_count')
    else:
        subject_count = 0
        student_counts = []

    start_date = today - timedelta(days=6)
    active_users_per_day = []
    for i in range(7):
        day = start_date + timedelta(days=i)
        sessions_on_day = sessions.filter(expire_date__date=day)
        user_ids_on_day = set()
        for session in sessions_on_day:
            session_data = session.get_decoded()
            user_id = session_data.get('_auth_user_id')
            if user_id:
                user_ids_on_day.add(user_id)
        unique_users_on_day = get_user_model().objects.filter(id__in=user_ids_on_day).distinct().count()
        active_users_per_day.append({'date': day, 'count': unique_users_on_day})

    articles = fetch_facebook_posts(request)

    context = {
        'active_users_count': active_users_count,
        'subject_count': subject_count,
        'student_counts': student_counts,
        'active_users_per_day': active_users_per_day,
        'articles': articles,
    }
    return render(request, 'accounts/dashboard.html', context)

def activity_stream(request):
    return render(request, 'accounts/activity_stream.html')

def assist(request):
    return render(request, 'accounts/assist.html')

def tools(request):
    return render(request, 'accounts/tools.html')

def createProfile(request):
    return render(request, 'accounts/createStudentProfile.html')

def sign_out(request):
    auth_logout(request)
    return redirect('admin_login_view')
