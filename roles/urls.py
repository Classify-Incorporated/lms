from django.urls import path
from .views import (
    createRole, updateRole, deleteRole, roleList
)

urlpatterns = [
    path('roleList/', roleList, name='roleList'),
    path('createRole/', createRole, name='createRole'), 
    path('updateRole/<int:pk>/', updateRole, name='updateRole'),
    path('deleteRole/<int:pk>/', deleteRole, name='deleteRole'),
]
