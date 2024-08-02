from django.shortcuts import render, get_object_or_404, redirect
from .models import Message, MessageReadStatus
from course.models import Course, SubjectEnrollment
from subject.models import Subject
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import JsonResponse
from accounts.models import CustomUser
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialToken

# Create your views here.
def send_message(request):
    if request.method == 'POST':
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        sender = request.user
        recipient_type = request.POST.get('recipient_type')

        recipients = []
        if recipient_type.startswith('course_'):
            course_id = recipient_type.split('_')[1]
            course = Course.objects.get(id=course_id)
            subject_enrollments = SubjectEnrollment.objects.filter(subjects__in=course.subjects.all()).distinct()
            recipients = [enrollment.student for enrollment in subject_enrollments]
        elif recipient_type.startswith('subject_'):
            subject_id = recipient_type.split('_')[1]
            subject = Subject.objects.get(id=subject_id)
            subject_enrollments = SubjectEnrollment.objects.filter(subjects=subject).distinct()
            recipients = [enrollment.student for enrollment in subject_enrollments]
        elif recipient_type.startswith('teacher_'):
            teacher_id = recipient_type.split('_')[1]
            teacher = CustomUser.objects.get(id=teacher_id)
            recipients = [teacher]

        message = Message.objects.create(subject=subject, body=body, sender=sender)
        message.recipients.set(recipients)
        message.save()

        print('Message sent successfully.')
        return redirect('inbox')

    courses = Course.objects.all()
    subjects = Subject.objects.all()
    instructors = CustomUser.objects.filter(groups__name='Instructor')

    unread_messages_count = MessageReadStatus.objects.filter(user=request.user, read_at__isnull=True).count()

    return render(request, 'message/message.html', {
        'courses': courses,
        'subjects': subjects,
        'instructors': instructors,
        'unread_messages_count': unread_messages_count,
    })



@login_required
def inbox(request):
    if not request.user.is_authenticated:
        return redirect('account_login')  # Ensure user is redirected to login if not authenticated

    print(f"Authenticated user: {request.user}")  # Verify user is authenticated

    messages = Message.objects.filter(recipients=request.user)
    print(f"Messages for user {request.user}: {messages}")  # Check retrieved messages

    unread_messages_count = MessageReadStatus.objects.filter(user=request.user, read_at__isnull=True).count()
    print(f"Unread messages count: {unread_messages_count}")

    message_status_list = []
    for message in messages:
        read_status = MessageReadStatus.objects.filter(message=message, user=request.user).first()
        message_status_list.append({
            'message': message,
            'read': read_status.read_at is not None if read_status else False
        })

    return render(request, 'message/inbox.html', {
        'message_status_list': message_status_list,
        'unread_messages_count': unread_messages_count,
    })



def view_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    read_status, created = MessageReadStatus.objects.get_or_create(user=request.user, message=message)

    if not read_status.read_at:
        read_status.read_at = timezone.now()
        read_status.save()

    return render(request, 'message/viewMessage.html', {'message': message})


def unread_count(request):
    unread_count = MessageReadStatus.objects.filter(user=request.user, read_at__isnull=True).count()
    return JsonResponse({'unread_count': unread_count})



def check_authentication(request):
    try:
        social_token = SocialToken.objects.get(account__user=request.user, account__provider='microsoft')
        access_token = social_token.token
        print(f"Access Token: {access_token}")
    except SocialToken.DoesNotExist:
        access_token = None
        print("Access Token not found")
    
    print(f"User: {request.user}")
    print(f"User is authenticated: {request.user.is_authenticated}")
    print(f"User email: {request.user.email}")
    
    data = {
        'user': str(request.user),
        'is_authenticated': request.user.is_authenticated,
        'email': request.user.email,
        'access_token': access_token,
    }
    return JsonResponse(data)