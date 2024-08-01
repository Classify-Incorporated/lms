from django.urls import path
from .views import (

    createModule, updateModule, viewModule, deleteModule
)

urlpatterns = [
    path('createModule/', createModule, name='createModule'),
    path('updateModule/<int:pk>/', updateModule, name='updateModule'),
    path('viewModule/<int:pk>/', viewModule, name='viewModule'),
    path('deleteModule/<int:pk>/', deleteModule, name='deleteModule'),


]
