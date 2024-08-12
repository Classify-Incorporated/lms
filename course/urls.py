from django.urls import path
from .views import (

    enrollStudent, subjectDetail, subjectStudentList, subjectList,createSemester,updateSemeter,semesterList,
    enrollStudentView,
)

urlpatterns = [
    path('enrollStudent/', enrollStudent, name='enrollStudent'),
    path('enrollStudentView/', enrollStudentView.as_view(), name='enrollStudentView'),

    path('SubjectList/', subjectList, name='SubjectList'),

    path('subjectDetail/<int:pk>/', subjectDetail, name='subjectDetail'),
    path('subjectStudentList/<int:pk>/students/', subjectStudentList, name='subjectStudentList'),

    # Semester Crud
    path('createSemester/', createSemester, name='createSemester'),
    path('updateSemeter/<int:pk>/', updateSemeter, name='updateSemeter'),
    path('semesterList/', semesterList, name='semesterList'),
]