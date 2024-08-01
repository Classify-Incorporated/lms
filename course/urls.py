from django.urls import path
from .views import (

    createCourse, updateCourse, viewCourse,courseList, EnrollStudentView,add_student_course

)

urlpatterns = [
    path('courseList/', courseList, name='courseList'), 
    path('createCourse/', createCourse, name='createCourse'),
    path('updateCourse/<int:pk>/', updateCourse, name='updateCourse'),
    path('viewCourse/<int:pk>/', viewCourse, name='viewCourse'), 

    path('enroll_student/', EnrollStudentView.as_view(), name='enroll_student'),
    path('add_student_course/', add_student_course, name='add_student_course'),

]
