from django.shortcuts import render, get_object_or_404, redirect
from .models import Message, MessageReadStatus, MessageUnreadStatus
from subject.models import Subject
from accounts.models import CustomUser
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialToken
from django.contrib import messages
from roles.models import Role
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import permission_required


@login_required
@permission_required('message.add_message', raise_exception=True)
def send_message(request):
    if request.method == 'POST':
        subject_text = request.POST.get('subject') 
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
        elif recipient_type.startswith('student_'):
            student_id = recipient_type.split('_')[1]
            student = get_object_or_404(CustomUser, id=student_id)
            recipients = [student]

        message = Message.objects.create(subject=subject_text, body=body, sender=sender)
        message.recipients.set(recipients)
        message.save()

        # Add entries to MessageUnreadStatus for each recipient
        for recipient in recipients:
            MessageUnreadStatus.objects.create(
                user=recipient,
                message=message,
                created_at=timezone.now()  # Set the timestamp for when the message was created
            )

        messages.success(request, 'Message sent successfully!')
        return redirect('inbox')
    else:
        messages.error(request, 'There was an error when sending the Message. Please try again.')

    subjects = Subject.objects.all()
    instructors = CustomUser.objects.filter(groups__name='Instructor')
    students = CustomUser.objects.filter(groups__name='Student')  # Fetch all students

    unread_messages_count = MessageReadStatus.objects.filter(user=request.user, read_at__isnull=True).count()

    return render(request, 'message/inbox.html', {
        'subjects': subjects,
        'instructors': instructors,
        'students': students,  # Pass students to the template
        'unread_messages_count': unread_messages_count,
    })

@login_required
def inbox(request):
    # Filter to only show messages that are not trashed
    messages = Message.objects.filter(recipients=request.user, is_trashed=False)
    
    message_status_list = []
    for message in messages:
        read_status = MessageReadStatus.objects.filter(message=message, user=request.user).first()
        message_status_list.append({
            'message': message,
            'read': read_status.read_at is not None if read_status else False
        })

    subjects = Subject.objects.all()
    instructor_role = Role.objects.get(name='Teacher')
    student_role = Role.objects.get(name='Student')
    instructors = CustomUser.objects.filter(profile__role=instructor_role) if instructor_role else CustomUser.objects.none()
    students = CustomUser.objects.filter(profile__role=student_role) if student_role else CustomUser.objects.none()

    return render(request, 'message/inbox.html', {
        'message_status_list': message_status_list,
        'subjects': subjects,
        'instructors': instructors,
        'students': students, 
    })


@login_required
@permission_required('message.view_message', raise_exception=True)
def view_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    # Get or create the read status entry
    read_status, created = MessageReadStatus.objects.get_or_create(user=request.user, message=message)
    
    # Update read status if it's not already marked as read
    if not read_status.read_at:
        read_status.read_at = timezone.now()
        read_status.save()

    # Remove the message from the MessageUnreadStatus table
    MessageUnreadStatus.objects.filter(user=request.user, message=message).delete()

    return render(request, 'message/viewMessage.html', {'message': message})

@login_required
def unread_count(request):
    unread_count = MessageReadStatus.objects.filter(user=request.user, read_at__isnull=True).count()
    return JsonResponse({'unread_count': unread_count})

@login_required
def check_authentication(request):
    try:
        social_token = SocialToken.objects.get(account__user=request.user, account__provider='microsoft')
        access_token = social_token.token
    except SocialToken.DoesNotExist:
        access_token = None


    data = {
        'user': str(request.user),
        'is_authenticated': request.user.is_authenticated,
        'email': request.user.email,
        'access_token': access_token,
    }
    return JsonResponse(data)

@login_required
def sent(request):
    # Filter messages where the sender is the logged-in user and are not trashed
    messages = Message.objects.filter(sender=request.user, is_trashed=False)

    message_status_list = []
    for message in messages:
        message_status_list.append({
            'message': message,
            'status': 'Sent'
        })

    subjects = Subject.objects.all()
    instructor_role = Role.objects.get(name='Teacher')
    student_role = Role.objects.get(name='Student')
    instructors = CustomUser.objects.filter(profile__role=instructor_role) if instructor_role else CustomUser.objects.none()
    students = CustomUser.objects.filter(profile__role=student_role) if student_role else CustomUser.objects.none()

    return render(request, 'message/sent.html', {
        'message_status_list': message_status_list,
        'subjects': subjects,
        'instructors': instructors,
        'students': students, 
    })

@login_required
def trash(request):
    # Filter messages where the logged-in user is a recipient and the message is trashed
    messages = Message.objects.filter(recipients=request.user, is_trashed=True)

    message_status_list = []
    for message in messages:
        message_status_list.append({
            'message': message,
            'status': 'Trashed'
        })

    subjects = Subject.objects.all()
    instructor_role = Role.objects.get(name='Teacher')
    student_role = Role.objects.get(name='Student')
    instructors = CustomUser.objects.filter(profile__role=instructor_role) if instructor_role else CustomUser.objects.none()
    students = CustomUser.objects.filter(profile__role=student_role) if student_role else CustomUser.objects.none()

    return render(request, 'message/trash.html', {
        'message_status_list': message_status_list,
        'subjects': subjects,
        'instructors': instructors,
        'students': students, 
    })


@csrf_exempt
@login_required
def trash_messages(request):
    if request.method == 'POST':
        message_ids = request.POST.getlist('message_ids[]')
        if message_ids:
            # Debugging statement to check if message_ids are being passed correctly
            print("Trashing messages with IDs:", message_ids)
            
            # Update the messages to set is_trashed=True
            update_count = Message.objects.filter(id__in=message_ids, recipients=request.user).update(is_trashed=True)
            
            # Debugging statement to check if the update was successful
            print("Number of messages updated:", update_count)
            
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No message IDs provided'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@csrf_exempt
@login_required
def untrash_messages(request):
    if request.method == 'POST':
        message_ids = request.POST.getlist('message_ids[]')
        if message_ids:
            # Update the is_trashed field to False where the logged-in user is a recipient
            Message.objects.filter(id__in=message_ids, recipients=request.user).update(is_trashed=False)
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No message IDs provided'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
