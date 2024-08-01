from django.contrib import admin
from .models import Course, SubjectEnrollment
# Register your models here.

admin.site.register(Course)
admin.site.register(SubjectEnrollment)