from django.urls import path
from .views import (

    add_course, updateCourse, viewCourse,courseList,add_regular_student, add_irregular_student_course,
    EnrollRegularStudentView, EnrollIrregularStudentView

)

urlpatterns = [
    path('courseList/', courseList, name='courseList'), 
    path('add_course/', add_course, name='add_course'),
    path('updateCourse/<int:pk>/', updateCourse, name='updateCourse'),
    path('viewCourse/<int:pk>/', viewCourse, name='viewCourse'),

    path('add_regular_student/', add_regular_student, name='add_regular_student'),
    path('add_irregular_student_course/', add_irregular_student_course, name='add_irregular_student_course'),

    path('enroll_regular_student/', EnrollRegularStudentView.as_view(), name='enroll_regular_student'),
    path('enroll_irregular_student/', EnrollIrregularStudentView.as_view(), name='enroll_irregular_student'),


]