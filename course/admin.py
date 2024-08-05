from django.contrib import admin
from .models import Course, SubjectEnrollment, Semester , Section
# Register your models here.

admin.site.register(Course)
admin.site.register(SubjectEnrollment)
admin.site.register(Semester)
admin.site.register(Section)