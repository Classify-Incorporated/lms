from django.urls import path
from .views import (

    createModule, updateModule, viewModule, deleteModule, moduleList,
    progressList, module_progress,  detailModuleProgress
)

urlpatterns = [
    path('moduleList/', moduleList, name='moduleList'),
    path('createModule/<int:subject_id>/',createModule, name='createModule'),
    path('updateModule/<int:pk>/', updateModule, name='updateModule'),
    path('viewModule/<int:pk>/', viewModule, name='viewModule'),
    path('deleteModule/<int:pk>/', deleteModule, name='deleteModule'),
    path('module_progress/', module_progress, name='module_progress'),
    path('progressList/', progressList, name='progressList'),
    path('detailProgress/module/<int:module_id>/', detailModuleProgress, name='detailModuleProgress'),

]
