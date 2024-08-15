from django.urls import path
from .views import (

    enrollStudent, subjectDetail, subjectStudentList, subjectList,createSemester,updateSemester,semesterList,
    createTerm,termList,updateTerm,subjectFinishedActivities,
    enrollStudentView,
)

urlpatterns = [
    path('enrollStudent/', enrollStudent, name='enrollStudent'),
    path('enrollStudentView/', enrollStudentView.as_view(), name='enrollStudentView'),

    path('SubjectList/', subjectList, name='SubjectList'),

    path('subjectDetail/<int:pk>/', subjectDetail, name='subjectDetail'),
    path('subjectFinishedActivities/<int:pk>/', subjectFinishedActivities, name='subjectFinishedActivities'),
    path('subjectStudentList/<int:pk>/', subjectStudentList, name='subjectStudentList'),

    # Semester Crud
    path('createSemester/', createSemester, name='createSemester'),
    path('updateSemester/<int:pk>/', updateSemester, name='updateSemester'),
    path('semesterList/', semesterList, name='semesterList'),

    # Term Crud
    path('createTerm/', createTerm, name='createTerm'),
    path('updateTerm/<int:pk>/', updateTerm, name='updateTerm'),
    path('termList/', termList, name='termList'),
]