from django.urls import path
from .views import (
viewGradeBookComponents, createGradeBookComponents, copyGradeBookComponents, updateGradeBookComponents, deleteGradeBookComponents,
teacherActivityView, studentActivityView, studentTotalScore, studentTotalScoreForActivityType, createTermGradeBookComponent, updateTermBookComponent,
deleteTermBookComponent, viewTermBookComponent, termBookList, studentTotalScoreApi, getSubjects, allowGradeVisibility, getSemesters,
excellingStudentsPerSubjectView, failingStudentsPerSubjectView

)

urlpatterns = [
    #gradebook crud
    path('viewGradeBookComponents/', viewGradeBookComponents, name='viewGradeBookComponents'), 
    path('createGradeBookComponents/', createGradeBookComponents, name='createGradeBookComponents'),
    path('copyGradeBookComponents/', copyGradeBookComponents, name='copyGradeBookComponents'),
    path('updateGradeBookComponents/<int:pk>/', updateGradeBookComponents, name='updateGradeBookComponents'),
    path('deleteGradeBookComponents/<int:pk>/', deleteGradeBookComponents, name='deleteGradeBookComponents'),

    #display score for student for each activity
    path('teacherActivityView/<int:activity_id>/', teacherActivityView, name='teacherActivityView'),
    path('studentActivityView/<int:activity_id>/', studentActivityView, name='studentActivityView'),

    #dislay student total score for a particular activity type
    path('studentTotalScore/<int:student_id>/<int:subject_id>/', studentTotalScore, name='studentTotalScore'),
    #dislay student total grade for a particular activity type
    path('studentTotalScoreForActivity/', studentTotalScoreForActivityType, name='studentTotalScoreForActivity'),

    #termbook crud
    path('termBookList/', termBookList, name='termBookList'),
    path('createTermGradeBookComponent/', createTermGradeBookComponent, name='createTermGradeBookComponent'),
    path('updateTermBookComponent/<int:id>/', updateTermBookComponent, name='updateTermBookComponent'),
    path('viewTermBookComponent/<int:id>/', viewTermBookComponent, name='viewTermBookComponent'),
    path('deleteTermBookComponent/<int:id>/', deleteTermBookComponent, name='deleteTermBookComponent'),

    #json api for fetching student total grade
    path('studentTotalScoreApi/', studentTotalScoreApi, name='studentTotalScoreApi'),

    #json format data
    path('getSubjects/', getSubjects, name='getSubjects'),
    path('getSemesters/', getSemesters, name='getSemesters'),

    #allow grade visibility
    path('allowGradeVisibility/<int:student_id>/', allowGradeVisibility, name='allowGradeVisibility'),


    path('failingStudentsPerSubject/', failingStudentsPerSubjectView, name='failingStudentsPerSubject'),
    path('excellingStudentsPerSubject/', excellingStudentsPerSubjectView, name='excellingStudentsPerSubject'),


]