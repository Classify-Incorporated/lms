from django.urls import path
from .views import (

    addCourse, updateCourse, viewCourse,courseList, addRegularStudent, addIrregularStudent,
    subjectDetail, courseStudentList, 
    EnrollRegularStudentView, EnrollIrregularStudentView,

    sectionList, createSection, updateSection

)

urlpatterns = [
    path('courseList/', courseList, name='courseList'), 
    path('addCourse/', addCourse, name='addCourse'),
    path('updateCourse/<int:pk>/', updateCourse, name='updateCourse'),
    path('viewCourse/<int:pk>/', viewCourse, name='viewCourse'),

    path('addRegularStudent/', addRegularStudent, name='addRegularStudent'),
    path('addIrregularStudent/', addIrregularStudent, name='addIrregularStudent'),

    path('subjectDetail/<int:pk>/', subjectDetail, name='subjectDetail'),
    path('courseStudentList/<int:pk>/', courseStudentList, name='courseStudentList'),

    path('enroll_regular_student/', EnrollRegularStudentView.as_view(), name='enroll_regular_student'),
    path('enroll_irregular_student/', EnrollIrregularStudentView.as_view(), name='enroll_irregular_student'),

    #Section List
    path('sectionList/', sectionList, name='sectionList'),
    path('createSection/', createSection, name='createSection'),
    path('updateSection/<int:id>/', updateSection, name='updateSection'),


]