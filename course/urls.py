from django.urls import path
from .views import (

    createCourse, updateCourse, viewCourse,courseList,add_regular_student, add_irregular_student_course,
    EnrollRegularStudentView, EnrollIrregularStudentView

)

urlpatterns = [
    path('courseList/', courseList, name='courseList'), 
    path('createCourse/', createCourse, name='createCourse'),
    path('updateCourse/<int:pk>/', updateCourse, name='updateCourse'),
    path('viewCourse/<int:pk>/', viewCourse, name='viewCourse'), 

    path('add_regular_student/', add_regular_student, name='add_regular_student'),
    path('add_irregular_student_course/', add_irregular_student_course, name='add_irregular_student_course'),

    path('enroll_regular_student/', EnrollRegularStudentView.as_view(), name='enroll_regular_student'),
    path('enroll_irregular_student/', EnrollIrregularStudentView.as_view(), name='enroll_irregular_student'),


]
