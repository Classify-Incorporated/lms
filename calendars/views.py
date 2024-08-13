from django.shortcuts import render
from activity.models import Activity,  StudentActivity
from django.http import JsonResponse
from subject.models import Subject
from django.utils import timezone

def calendars(request):
    return render(request, 'calendar/calendar.html')

def activity_api(request):
    user = request.user
    events = []  # Use a list to store events

    if user.profile.role.name.lower() == 'student':
        # Filter activities based on the student's enrolled subjects
        student_activities = StudentActivity.objects.filter(student=user)
        for student_activity in student_activities:
            activity = student_activity.activity
            event = {
                'id': activity.id,  # Ensure the ID is included here
                'title': activity.activity_name,
                'start': activity.start_time.isoformat() if activity.start_time else '',
                'end': activity.end_time.isoformat() if activity.end_time else '',
                'allDay': activity.start_time is None or activity.end_time is None,
            }
            events.append(event)

    elif user.profile.role.name.lower() == 'teacher':
        # Filter activities based on the teacher's assigned subjects
        teacher_activities = Activity.objects.filter(subject__assign_teacher=user)
        for activity in teacher_activities:
            event = {
                'id': activity.id,  # Ensure the ID is included here
                'title': activity.activity_name,
                'start': activity.start_time.isoformat() if activity.start_time else '',
                'end': activity.end_time.isoformat() if activity.end_time else '',
                'allDay': activity.start_time is None or activity.end_time is None,
            }
            events.append(event)

    return JsonResponse(events, safe=False)