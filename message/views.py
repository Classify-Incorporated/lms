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
from course.models import Semester
from django.db.models import Q

@login_required
@permission_required('message.add_message', raise_exception=True)
def send_message(request, parent_id=None):
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

        message = Message.objects.create(
            subject=subject_text,
            body=body,
            sender=sender,
            parent=parent_id if parent_id else None  # Link to parent if provided
        )
        message.recipients.set(recipients)
        message.save()

        # Create unread status for the recipient, not for the sender
        for recipient in recipients:
            MessageUnreadStatus.objects.create(
                user=recipient,
                message=message,
                created_at=timezone.now()
            )

        messages.success(request, 'Message sent successfully!')
        return redirect('inbox')
    else:
        messages.error(request, 'There was an error when sending the message. Please try again.')

    subjects = Subject.objects.all()
    instructors = CustomUser.objects.filter(groups__name='Instructor')
    students = CustomUser.objects.filter(groups__name='Student')

    return render(request, 'message/inbox.html', {
        'subjects': subjects,
        'instructors': instructors,
        'students': students,
    })

@login_required
def inbox(request):
    messages = Message.objects.filter(
        (Q(recipients=request.user) | Q(sender=request.user)) & Q(is_trashed=False) & Q(parent__isnull=True)
    ).distinct().order_by('-timestamp')

    unread_messages_count = MessageUnreadStatus.objects.filter(
        user=request.user, created_at__isnull=False  # Count only unread messages
    ).count()

    request.session['unread_messages_count'] = unread_messages_count

    message_status_list = []
    for message in messages:
        read_status = MessageReadStatus.objects.filter(message=message, user=request.user).first()
        reply_count = message.replies.count()

        message_status_list.append({
            'message': message,
            'read': read_status.read_at is not None if read_status else False,
            'reply_count': reply_count
        })
        
    # Get the current semester
    today = timezone.now().date()
    current_semester = Semester.objects.filter(start_date__lte=today, end_date__gte=today).first()

    # Initialize variables for subjects, instructors, and students
    subjects = Subject.objects.none()
    instructors = CustomUser.objects.none()
    students = CustomUser.objects.none()

    # Get the user's role (Teacher or Student)
    user = request.user
    instructor_role = None
    student_role = None

    # Retrieve instructor and student roles if they exist
    try:
        instructor_role = Role.objects.get(name='Teacher')
    except Role.DoesNotExist:
        pass  # Handle missing 'Teacher' role gracefully

    try:
        student_role = Role.objects.get(name='Student')
    except Role.DoesNotExist:
        pass 

    # Filter subjects based on user role and current semester
    if current_semester:
        if hasattr(user, 'profile') and user.profile.role:
            user_role = user.profile.role
            if instructor_role and user_role == instructor_role:
                # If the user is a teacher, filter subjects where the teacher is assigned
                subjects = Subject.objects.filter(assign_teacher=user, subjectenrollment__semester=current_semester).distinct()
            elif student_role and user_role == student_role:
                # If the user is a student, filter subjects where the student is enrolled
                subjects = Subject.objects.filter(subjectenrollment__student=user, subjectenrollment__semester=current_semester).distinct()
            else:
                # If the user is an admin or another role, show all subjects for the current semester
                subjects = Subject.objects.filter(subjectenrollment__semester=current_semester).distinct()

        # Retrieve all instructors and students for the current semester
        if instructor_role:
            instructors = CustomUser.objects.filter(profile__role=instructor_role).distinct()
        if student_role:
            students = CustomUser.objects.filter(profile__role=student_role).distinct()

    return render(request, 'message/inbox.html', {
        'message_status_list': message_status_list,
        'subjects': subjects,
        'instructors': instructors,
        'students': students,
        'unread_messages_count': unread_messages_count,
    })

@login_required
@permission_required('message.view_message', raise_exception=True)
def view_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    # Ensure the user is authorized to view the message
    if not (message.recipients.filter(id=request.user.id).exists() or message.sender == request.user):
        messages.error(request, "You are not authorized to view this message.")
        return redirect('inbox')

    # Mark the message as read for the recipient or sender viewing the message
    if request.user in message.recipients.all() or request.user == message.sender:
        read_status, created = MessageReadStatus.objects.get_or_create(user=request.user, message=message)
        if not read_status.read_at:
            read_status.read_at = timezone.now()
            read_status.save()

        # Update (but do not delete) the unread status for the recipient or sender
        MessageUnreadStatus.objects.filter(user=request.user, message=message).update(created_at=None)

    # Retrieve all replies
    replies = message.replies.all().order_by('timestamp')

    return render(request, 'message/viewMessage.html', {
        'message': message,
        'replies': replies,
    })
    
def get_all_replies(message):
    """
    Recursively retrieve all replies to a message.
    """
    replies = []
    direct_replies = message.replies.all().order_by('timestamp')
    for reply in direct_replies:
        reply_replies = get_all_replies(reply)
        replies.append({
            'message': reply,
            'replies': reply_replies
        })
    return replies

@login_required
@permission_required('message.view_message', raise_exception=True)
def view_sent_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    recipients = message.recipients.all()  # Get all recipients

    return render(request, 'message/viewSentMessage.html', {
        'message': message,
        'recipients': recipients
    })

@login_required
@permission_required('message.add_message', raise_exception=True)
def reply_message(request, message_id):
    original_message = get_object_or_404(Message, id=message_id)

    if request.method == 'POST':
        body = request.POST.get('body')
        sender = request.user

        # Determine the recipient
        recipient = original_message.sender if sender != original_message.sender else original_message.recipients.first()

        # Create the reply and link it to the parent message
        reply_message = Message.objects.create(
            subject=f"Re: {original_message.subject}",
            body=body,
            sender=sender,
            parent=original_message  # Link the reply to the parent message
        )
        reply_message.recipients.set([recipient])
        reply_message.save()

        # Update unread status for the original sender
        MessageUnreadStatus.objects.update_or_create(
            user=recipient, message=original_message, defaults={'created_at': timezone.now()}
        )

        messages.success(request, 'Your reply has been sent successfully!')
        return redirect('inbox')

    return render(request, 'message/reply.html', {
        'original_message': original_message,
    })

    
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

    # Get unread messages count
    unread_messages_count = MessageReadStatus.objects.filter(user=request.user, read_at__isnull=True).count()

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
        'unread_messages_count': unread_messages_count  # Pass unread messages count to the template
    })

@login_required
def trash(request):
    # Filter messages where the logged-in user is either a recipient or the sender, and the message is trashed
    trashed_messages = Message.objects.filter(
        is_trashed=True
    ).filter(
        Q(recipients=request.user) | Q(sender=request.user)
    ).distinct()

    message_status_list = []
    for message in trashed_messages:
        message_status_list.append({
            'message': message,
            'status': 'Trashed'
        })

    # Get unread messages count
    unread_messages_count = MessageReadStatus.objects.filter(user=request.user, read_at__isnull=True).count()

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
        'unread_messages_count': unread_messages_count  # Pass unread messages count to the template
    })

@csrf_exempt
@login_required
def trash_messages(request):
    if request.method == 'POST':
        message_ids = request.POST.getlist('message_ids[]')
        if message_ids:
            # Debugging statement to check if message_ids are being passed correctly
            print("Trashing messages with IDs:", message_ids)
            
            # Update the messages where the logged-in user is a recipient to set is_trashed=True
            received_update_count = Message.objects.filter(id__in=message_ids, recipients=request.user).update(is_trashed=True)

            # Update the messages where the logged-in user is the sender to set is_trashed=True
            sent_update_count = Message.objects.filter(id__in=message_ids, sender=request.user).update(is_trashed=True)

            # Debugging statement to check if the update was successful
            print(f"Number of received messages updated: {received_update_count}")
            print(f"Number of sent messages updated: {sent_update_count}")

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
            received_update_count = Message.objects.filter(id__in=message_ids, recipients=request.user).update(is_trashed=False)

            # Update the is_trashed field to False where the logged-in user is the sender
            sent_update_count = Message.objects.filter(id__in=message_ids, sender=request.user).update(is_trashed=False)

            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No message IDs provided'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

