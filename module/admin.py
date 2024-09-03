from django.contrib import admin
from .models import Module, SCORMPackage, StudentProgress
# Register your models here.

admin.site.register(Module)
admin.site.register(SCORMPackage)
admin.site.register(StudentProgress)