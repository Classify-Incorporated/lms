from django.urls import path
from .views import (
    AddActivityView, AddQuizTypeView, AddQuestionView, DisplayQuestionsView, GradeIndividualEssayView,
    SubmitAnswersView, GradeEssayView, SaveAllQuestionsView,ActivityDetailView,DeleteTempQuestionView,
    activityCompletedView, studentQuizzesExams, deleteActivityView, UpdateActivity
)

urlpatterns = [
    path('add_activity/<int:subject_id>/', AddActivityView.as_view(), name='add_activity'),
    path('quiz_type/<int:activity_id>/', AddQuizTypeView.as_view(), name='add_quiz_type'),
    path('add_question/<int:activity_id>/<int:quiz_type_id>/', AddQuestionView.as_view(), name='add_question'),
    path('delete_temp_question/<int:activity_id>/<int:index>/', DeleteTempQuestionView.as_view(), name='delete_temp_question'),
    path('display_question/<int:activity_id>/', DisplayQuestionsView.as_view(), name='display_question'),
    path('submit_answers/<int:activity_id>/', SubmitAnswersView.as_view(), name='submit_answers'),
    path('grade_essays/<int:activity_id>/', GradeEssayView.as_view(), name='grade_essays'),
    path('grade_individual_essay/<int:activity_id>/<int:student_question_id>/', GradeIndividualEssayView.as_view(), name='grade_individual_essay'),
    path('save_all_questions/<int:activity_id>/', SaveAllQuestionsView.as_view(), name='save_all_questions'),
    path('UpdateActivity/<int:activity_id>/', UpdateActivity, name='UpdateActivity'),

    path('activity_completed/<int:score>/<int:activity_id>/<str:show_score>/', activityCompletedView, name='activity_completed'),
    path('studentQuizzesExams/', studentQuizzesExams, name='studentQuizzesExams'),
    path('activity_detail/<int:activity_id>/', ActivityDetailView.as_view(), name='activity_detail'),

    path('deleteActivityView/<int:activity_id>/', deleteActivityView, name='deleteActivityView'),
    
]