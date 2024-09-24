from django.contrib import admin
from .models import CustomUser, Profile

@admin.register(CustomUser)
class ProjectAdmin(admin.ModelAdmin):
    search_fields = ('id', 'email',)
    list_display = ('id', 'email')

@admin.register(Profile)
class ProjectAdmin(admin.ModelAdmin):
    search_fields = ('id', 'first_name','last_name')
    list_display = ('id', 'user','role','first_name','last_name')