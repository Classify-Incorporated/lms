from django.contrib import admin
from .models import SubjectLog, UserSubjectLog
# Register your models here.

class SubjectLogAdmin(admin.ModelAdmin):
    fields = ('subject', 'message','activity')
    list_display = ('subject', 'message', 'created_at','activity')

admin.site.register(SubjectLog, SubjectLogAdmin)


admin.site.register(UserSubjectLog)

