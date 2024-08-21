from django.contrib import admin
from .models import SubjectLog
# Register your models here.

class SubjectLogAdmin(admin.ModelAdmin):
    fields = ('subject', 'message')
    list_display = ('subject', 'message', 'created_at')

admin.site.register(SubjectLog, SubjectLogAdmin)