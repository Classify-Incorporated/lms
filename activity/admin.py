from django.contrib import admin
from .models import Activity, ActivityType , QuizType, ActivityQuestion, StudentActivity, StudentQuestion
# Register your models here.
admin.site.register(Activity)
admin.site.register(ActivityType)
admin.site.register(QuizType)
admin.site.register(ActivityQuestion)
admin.site.register(StudentActivity)
admin.site.register(StudentQuestion)
