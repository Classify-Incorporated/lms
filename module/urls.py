from django.urls import path
from .views import (

    createModule, updateModule, viewModule, deleteModule, moduleList,
    uploadScormPackage, updateScormPackage, deleteScormPackage
)

urlpatterns = [
    path('moduleList/', moduleList, name='moduleList'),
    path('createModule/<int:subject_id>/',createModule, name='createModule'),
    path('updateModule/<int:pk>/', updateModule, name='updateModule'),
    path('viewModule/<int:pk>/', viewModule, name='viewModule'),
    path('deleteModule/<int:pk>/', deleteModule, name='deleteModule'),

    path('upload/<int:subject_id>/', uploadScormPackage, name='upload'),
    path('updateScormPackage/<int:id>/', updateScormPackage, name='updateScormPackage'),
    path('deleteScormPackage/<int:id>/', deleteScormPackage, name='deleteScormPackage'),

]
