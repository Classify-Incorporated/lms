from django.urls import path
from .views import (

    createModule, updateModule, viewModule, deleteModule, moduleList,
    uploadScormPackage, updateScormPackage, deleteScormPackage, test_scorm_connection,
    list_scorm_courses, create_and_launch_scorm,view_registration_data, list_registration_ids,
    scormRegistration, detailRegistration
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
    path('test_scorm/', test_scorm_connection, name='test_scorm_connection'),
    path('list_scorm_courses/', list_scorm_courses, name='list_scorm_courses'),
    path('launch_scorm/<int:scorm_id>/', create_and_launch_scorm, name='create_and_launch_scorm'),
    path('view_registration_data/<str:registration_id>/', view_registration_data, name='view_registration_data'),
    path('list_registration_ids/', list_registration_ids, name='list_registration_ids'),

    path('scormRegistration/', scormRegistration, name='scormRegistration'),
    path('detailRegistration/<str:registration_id>/', detailRegistration, name='detailRegistration'),
]
