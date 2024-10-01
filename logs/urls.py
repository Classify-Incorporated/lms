from django.urls import path
from .views import (
    subjectLogDetails, mark_log_as_read
)

urlpatterns = [
    path('subjectLogDetails/', subjectLogDetails, name='subjectLogDetails'),
    path('logs/read/<int:log_id>/', mark_log_as_read, name='mark_log_as_read'),
]
