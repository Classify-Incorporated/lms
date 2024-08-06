from django.urls import path
from .views import (
viewGradeBookComponents, createGradeBookComponents, updateGradeBookComponents, deleteGradeBookComponents, viewGradeBookComponents

)

urlpatterns = [
    path('viewGradeBookComponents/', viewGradeBookComponents, name='viewGradeBookComponents'), 
    path('createGradeBookComponents/', createGradeBookComponents, name='createGradeBookComponents'),
    path('updateGradeBookComponents/<int:pk>/', updateGradeBookComponents, name='updateGradeBookComponents'),
    path('deleteGradeBookComponents/<int:pk>/', deleteGradeBookComponents, name='deleteGradeBookComponents'),
    path('viewGradeBookComponents/', viewGradeBookComponents, name='viewGradeBookComponents'),
]