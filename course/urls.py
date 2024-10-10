from django.urls import path
from .views import (

    enrollStudent, subjectDetail, subjectStudentList, subjectList,createSemester,updateSemester,semesterList,endSemester,
    previousSemestersView, createTerm,termList,updateTerm,subjectFinishedActivities, selectParticipation,
    enrollStudentView, subjectEnrollmentList, dropStudentFromSubject, deleteStudentFromSubject, CopyActivitiesView, termActivitiesGraph,
    displayActivitiesForTerm, delete_semester, deleteTerm, record_attendance, attendanceList, updateAttendace
)

urlpatterns = [
    #enrolled student
    path('enrollStudent/', enrollStudent, name='enrollStudent'),
    path('enrollStudentView/', enrollStudentView.as_view(), name='enrollStudentView'),
    path('dropStudentFromSubject/<int:enrollment_id>/', dropStudentFromSubject, name='dropStudentFromSubject'),
    path('deleteStudentFromSubject/<int:enrollment_id>/', deleteStudentFromSubject, name='deleteStudentFromSubject'),
    path('subjectEnrollmentList/', subjectEnrollmentList, name='subjectEnrollmentList'),

    path('SubjectList/', subjectList, name='SubjectList'),

    path('subjectDetail/<int:pk>/', subjectDetail, name='subjectDetail'),
    path('subjectFinishedActivities/<int:pk>/', subjectFinishedActivities, name='subjectFinishedActivities'),
    path('subjectStudentList/<int:pk>/', subjectStudentList, name='subjectStudentList'),

    # Semester Crud
    path('createSemester/', createSemester, name='createSemester'),
    path('updateSemester/<int:pk>/', updateSemester, name='updateSemester'),
    path('semesterList/', semesterList, name='semesterList'),
    path('delete_semester/<int:pk>/', delete_semester, name='delete_semester'),
    path('endSemester/<int:pk>/', endSemester, name='endSemester'),

    path('previousSemestersView/', previousSemestersView, name='previousSemestersView'),

    # Term Crud
    path('createTerm/', createTerm, name='createTerm'),
    path('updateTerm/<int:pk>/', updateTerm, name='updateTerm'),
    path('deleteTerm/<int:pk>/', deleteTerm, name='deleteTerm'),
    path('termList/', termList, name='termList'),
    path('displayActivitiesForTerm/<int:term_id>/<str:activity_type>/<int:subject_id>/<str:activity_name>/', displayActivitiesForTerm, name='displayActivitiesForTerm'),

    # Participation Scores
    path('selectParticipation/<int:subject_id>/', selectParticipation, name='selectParticipation'),
    # Copy data from previous semester to new semester
    path('subject/<int:subject_id>/copy_activities/', CopyActivitiesView.as_view(), name='copy_activities'),

    path('termActivitiesGraph/<int:subject_id>/', termActivitiesGraph, name='termActivitiesGraph'),

    path('attendance/record/<int:subject_id>/', record_attendance, name='record_attendance'),
    path('attendanceList/<int:subject_id>/', attendanceList, name='attendanceList'),
    path('updateAttendace/<int:id>/', updateAttendace, name='updateAttendace'),
]