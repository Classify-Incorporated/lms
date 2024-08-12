from django.contrib import admin
from .models import SubjectEnrollment, Semester, Term
# Register your models here.

admin.site.register(SubjectEnrollment)
admin.site.register(Semester)
admin.site.register(Term)