from django.contrib import admin
from .models import GradeBookComponents, TermGradeBookComponents, SubGradeBook


admin.site.register(GradeBookComponents)
admin.site.register(TermGradeBookComponents)
admin.site.register(SubGradeBook)