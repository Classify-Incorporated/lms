# context_processors.py
from .models import SubjectLog, UserSubjectLog
from course.models import SubjectEnrollment
from subject.models import Subject

def subject_logs(request):
    if request.user.is_authenticated:
        user_role = request.user.profile.role.name.lower()

        # Only show logs to students and teachers
        show_logs = user_role in ['student', 'teacher']  # True if user is student or teacher
        
        logs = []
        unread_notifications_count = 0

        if show_logs:
            if user_role == 'student':
                # Get the subjects the student is enrolled in
                enrolled_subjects = SubjectEnrollment.objects.filter(student=request.user).values_list('subject', flat=True)
                logs = SubjectLog.objects.filter(activity=True, subject__in=enrolled_subjects).order_by('-created_at')[:5]
            elif user_role == 'teacher':
                # Get the subjects the teacher is assigned to
                teaching_subjects = Subject.objects.filter(assign_teacher=request.user).values_list('id', flat=True)
                logs = SubjectLog.objects.filter(activity=True, subject__in=teaching_subjects).order_by('-created_at')[:5]

            # For each log, check if it has been read by the current user
            unread_logs = []
            for log in logs:
                user_log, created = UserSubjectLog.objects.get_or_create(user=request.user, subject_log=log)
                if not user_log.read:
                    unread_logs.append(log)

            unread_notifications_count = len(unread_logs)

        return {
            'show_logs': show_logs,
            'logs': logs,
            'unread_notifications_count': unread_notifications_count
        }
    return {}