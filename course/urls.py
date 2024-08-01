from django.urls import path
from .views import (

    createCourse, updateCourse, viewCourse,courseList
)

urlpatterns = [
    path('courseList/', courseList, name='courseList'), 
    path('createCourse/', createCourse, name='createCourse'),
    path('updateCourse/<int:pk>/', updateCourse, name='updateCourse'),
    path('viewCourse/<int:pk>/', viewCourse, name='viewCourse'), 

]
