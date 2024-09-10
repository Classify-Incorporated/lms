from django.urls import path
from .views import (

    enrollStudent, subjectDetail, subjectStudentList, subjectList,createSemester,updateSemester,semesterList,
    createTerm,termList,updateTerm,subjectFinishedActivities, selectParticipation,
    enrollStudentView, subjectEnrollmentList, dropStudentFromSubject, 
)

urlpatterns = [
    #enrolled student
    path('enrollStudent/', enrollStudent, name='enrollStudent'),
    path('enrollStudentView/', enrollStudentView.as_view(), name='enrollStudentView'),
    path('dropStudentFromSubject/<int:enrollment_id>/', dropStudentFromSubject, name='dropStudentFromSubject'),
    path('subjectEnrollmentList/', subjectEnrollmentList, name='subjectEnrollmentList'),

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

    # Participation Scores
    path('selectParticipation/<int:subject_id>/', selectParticipation, name='selectParticipation'),
]