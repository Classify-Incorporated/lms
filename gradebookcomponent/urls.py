from django.urls import path
from .views import (
viewGradeBookComponents, createGradeBookComponents, updateGradeBookComponents, deleteGradeBookComponents,
student_grade_view, all_students_activity_scores_view, teacherActivityView, studentActivityView, studentTotalScore

)

urlpatterns = [
    path('viewGradeBookComponents/', viewGradeBookComponents, name='viewGradeBookComponents'), 
    path('createGradeBookComponents/', createGradeBookComponents, name='createGradeBookComponents'),
    path('updateGradeBookComponents/<int:pk>/', updateGradeBookComponents, name='updateGradeBookComponents'),
    path('deleteGradeBookComponents/<int:pk>/', deleteGradeBookComponents, name='deleteGradeBookComponents'),

    path('student_grade_view/', student_grade_view, name='student_grade_view'),
    path('all_students_activity_scores_view/', all_students_activity_scores_view, name='all_students_activity_scores_view'),
    path('teacherActivityView/<int:activity_id>/', teacherActivityView, name='teacherActivityView'),
    path('studentActivityView/<int:activity_id>/', studentActivityView, name='studentActivityView'),

    path('studentTotalScore/', studentTotalScore, name='studentTotalScore'),
]