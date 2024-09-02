from django.urls import path
from .views import (

    createModule, updateModule, viewModule, deleteModule, moduleList,
    uploadPackage, deletePackage,updatePackage,view_scorm_package,
)

urlpatterns = [
    path('moduleList/', moduleList, name='moduleList'),
    path('createModule/<int:subject_id>/',createModule, name='createModule'),
    path('updateModule/<int:pk>/', updateModule, name='updateModule'),
    path('viewModule/<int:pk>/', viewModule, name='viewModule'),
    path('deleteModule/<int:pk>/', deleteModule, name='deleteModule'),
    path('uploadPackage/<int:subject_id>/', uploadPackage, name='uploadPackage'),
    path('deletePackage/<int:id>/', deletePackage, name='deletePackage'),
    path('updatePackage/<int:id>/', updatePackage, name='updatePackage'),
    path('view_scorm_package/<int:id>/', view_scorm_package, name='view_scorm_package'),

]
