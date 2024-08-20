from django.urls import path
from .views import (
    createSubject, updateSubject, deleteSubject, subjectList
)

urlpatterns = [
    path('subject/', subjectList, name='subject'),
    path('createSubject/', createSubject, name='createSubject'), 
    path('updateSubject/<int:pk>/', updateSubject, name='updateSubject'),
    path('deleteSubject/<int:pk>/', deleteSubject, name='deleteSubject'),



]