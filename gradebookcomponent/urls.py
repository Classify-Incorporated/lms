from django.urls import path
from .views import (
viewGradeBookComponents, createGradeBookComponents, copyGradeBookComponents, updateGradeBookComponents, deleteGradeBookComponents,
teacherActivityView, studentActivityView, studentTotalScore, studentTotalScoreForActivityType, createTermGradeBookComponent, termBookList,
studentTotalScoreApi, get_terms

)

urlpatterns = [
    path('viewGradeBookComponents/', viewGradeBookComponents, name='viewGradeBookComponents'), 
    path('createGradeBookComponents/', createGradeBookComponents, name='createGradeBookComponents'),
    path('copyGradeBookComponents/', copyGradeBookComponents, name='copyGradeBookComponents'),
    path('updateGradeBookComponents/<int:pk>/', updateGradeBookComponents, name='updateGradeBookComponents'),
    path('deleteGradeBookComponents/<int:pk>/', deleteGradeBookComponents, name='deleteGradeBookComponents'),

    path('teacherActivityView/<int:activity_id>/', teacherActivityView, name='teacherActivityView'),
    path('studentActivityView/<int:activity_id>/', studentActivityView, name='studentActivityView'),

    path('studentTotalScore/', studentTotalScore, name='studentTotalScore'),
    path('studentTotalScoreForActivity/', studentTotalScoreForActivityType, name='studentTotalScoreForActivity'),

    path('termBookList/', termBookList, name='termBookList'),
    path('createTermGradeBookComponent/', createTermGradeBookComponent, name='createTermGradeBookComponent'),

    path('studentTotalScoreApi/', studentTotalScoreApi, name='studentTotalScoreApi'),
    path('getTerms/', get_terms, name='getTerms'),

]