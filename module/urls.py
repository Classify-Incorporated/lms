from django.urls import path
from .views import (

    createModule, updateModule, viewModule, deleteModule, moduleList,
    upload_scorm_package
)

urlpatterns = [
    path('moduleList/', moduleList, name='moduleList'),
    path('createModule/<int:subject_id>/',createModule, name='createModule'),
    path('updateModule/<int:pk>/', updateModule, name='updateModule'),
    path('viewModule/<int:pk>/', viewModule, name='viewModule'),
    path('deleteModule/<int:pk>/', deleteModule, name='deleteModule'),

    path('upload/<int:subject_id>/', upload_scorm_package, name='upload'),

]
