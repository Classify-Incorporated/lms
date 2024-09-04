from django.urls import path
from .views import (
    createSubject, updateSubject, deleteSubject, subjectList,
    check_duplicate_subject
)

urlpatterns = [
    path('subject/', subjectList, name='subject'),
    path('createSubject/', createSubject, name='createSubject'), 
    path('updateSubject/<int:pk>/', updateSubject, name='updateSubject'),
    path('deleteSubject/<int:pk>/', deleteSubject, name='deleteSubject'),
    path('check-duplicate-subject/', check_duplicate_subject, name='check_duplicate_subject'),



]