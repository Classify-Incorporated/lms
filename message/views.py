from django.shortcuts import render, get_object_or_404, redirect
from .models import Message, MessageReadStatus
from subject.models import Subject
from accounts.models import CustomUser
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialToken

@login_required
def send_message(request):
    if request.method == 'POST':
        subject_text = request.POST.get('subject')  # Renamed to avoid conflict with Subject model
        body = request.POST.get('body')
        sender = request.user
        recipient_type = request.POST.get('recipient_type')

        recipients = []
        if recipient_type.startswith('subject_'):
            subject_id = recipient_type.split('_')[1]
            subject = get_object_or_404(Subject, id=subject_id)
            subject_enrollments = subject.subjectenrollment_set.all().distinct()
            recipients = [enrollment.student for enrollment in subject_enrollments]
        elif recipient_type.startswith('teacher_'):
            teacher_id = recipient_type.split('_')[1]
            teacher = get_object_or_404(CustomUser, id=teacher_id)
            recipients = [teacher]

        message = Message.objects.create(subject=subject_text, body=body, sender=sender)
        message.recipients.set(recipients)
        message.save()

        print('Message sent successfully.')
        return redirect('inbox')

    subjects = Subject.objects.all()
    instructors = CustomUser.objects.filter(groups__name='Instructor')

    unread_messages_count = MessageReadStatus.objects.filter(user=request.user, read_at__isnull=True).count()

    return render(request, 'message/inbox.html', {
        'subjects': subjects,
        'instructors': instructors,
        'unread_messages_count': unread_messages_count,
    })

@login_required
def inbox(request):
    if not request.user.is_authenticated:
        return redirect('account_login')  # Ensure user is redirected to login if not authenticated

    messages = Message.objects.filter(recipients=request.user)
    unread_messages_count = MessageReadStatus.objects.filter(user=request.user, read_at__isnull=True).count()

    message_status_list = []
    for message in messages:
        read_status = MessageReadStatus.objects.filter(message=message, user=request.user).first()
        message_status_list.append({
            'message': message,
            'read': read_status.read_at is not None if read_status else False
        })

    subjects = Subject.objects.all()
    instructors = CustomUser.objects.filter(groups__name='Instructor')

    return render(request, 'message/inbox.html', {
        'message_status_list': message_status_list,
        'unread_messages_count': unread_messages_count,
        'subjects': subjects,
        'instructors': instructors,
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
