from django.urls import path
from .views import (

    add_course, updateCourse, viewCourse,courseList,

)

urlpatterns = [
    path('courseList/', courseList, name='courseList'), 
    path('add_course/', add_course, name='add_course'),
    path('updateCourse/<int:pk>/', updateCourse, name='updateCourse'),
    path('viewCourse/<int:pk>/', viewCourse, name='viewCourse'),


]