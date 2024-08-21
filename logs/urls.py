from django.urls import path
from .views import (
    subjectLogDetails
)

urlpatterns = [
    path('subjectLogDetails/', subjectLogDetails, name='subjectLogDetails'),
]
