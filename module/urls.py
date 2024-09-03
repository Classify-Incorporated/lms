from django.urls import path
from .views import (

    createModule, updateModule, viewModule, deleteModule, moduleList,
    uploadPackage, deletePackage,updatePackage,viewScormPackage,
)

urlpatterns = [
    path('moduleList/', moduleList, name='moduleList'),
    path('createModule/<int:subject_id>/',createModule, name='createModule'),
    path('updateModule/<int:pk>/', updateModule, name='updateModule'),
    path('viewModule/<int:pk>/', viewModule, name='viewModule'),
    path('deleteModule/<int:pk>/', deleteModule, name='deleteModule'),
    path('upload/<int:subject_id>/', uploadPackage, name='upload'),
    path('deletePackage/<int:id>/', deletePackage, name='deletePackage'),
    path('updatePackage/<int:id>/', updatePackage, name='updatePackage'),
    path('viewScormPackage/<int:id>/', viewScormPackage, name='viewScormPackage'),

]
