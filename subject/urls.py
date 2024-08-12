from django.urls import path
from .views import (
    createSubject, updateSubject, deleteSubject, viewSubject, subjectList
)

urlpatterns = [
    path('subject/', subjectList, name='subject'),
    path('createSubject/', createSubject, name='createSubject'), 
    path('updateSubject/<int:pk>/', updateSubject, name='updateSubject'),
    path('viewSubject/<int:pk>/', viewSubject, name='viewSubject'),
    path('deleteSubject/<int:pk>/', deleteSubject, name='deleteSubject'),



]