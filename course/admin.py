from django.contrib import admin
from .models import SubjectEnrollment, Semester, Term, StudentParticipationScore, Attendance, AttendanceStatus, Retake
# Register your models here.

admin.site.register(SubjectEnrollment)
admin.site.register(Semester)
admin.site.register(Term)
admin.site.register(StudentParticipationScore)
admin.site.register(Attendance)
admin.site.register(AttendanceStatus)
admin.site.register(Retake)
