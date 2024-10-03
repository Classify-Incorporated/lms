from django.urls import path
from .views import (
    AddActivityView, AddQuizTypeView, AddQuestionView, DisplayQuestionsView, GradeIndividualEssayView,
    SubmitAnswersView, GradeEssayView, SaveAllQuestionsView,ActivityDetailView,DeleteTempQuestionView,
    UpdateQuestionView,RetakeActivityView,  toggleShowScore,
    activityCompletedView, deleteActivityView, UpdateActivity, activityList, deleteActivity,
    activityTypeList, createActivityType, updateActivityType, deleteActivityType, participation_scores
)

urlpatterns = [
    path('subject/<int:subject_id>/add_activity/', AddActivityView.as_view(), name='add_activity'),
    path('quiz_type/<int:activity_id>/', AddQuizTypeView.as_view(), name='add_quiz_type'),
    path('add_question/<int:activity_id>/<int:quiz_type_id>/', AddQuestionView.as_view(), name='add_question'),
    path('delete_temp_question/<int:activity_id>/<int:index>/', DeleteTempQuestionView.as_view(), name='delete_temp_question'),
    path('edit_question/<int:activity_id>/<int:index>/', UpdateQuestionView.as_view(), name='edit_question'),
    path('display_question/<int:activity_id>/', DisplayQuestionsView.as_view(), name='display_question'),
    path('submit_answers/<int:activity_id>/', SubmitAnswersView.as_view(), name='submit_answers'),
    path('grade_essays/<int:activity_id>/', GradeEssayView.as_view(), name='grade_essays'),
    path('grade_individual_essay/<int:activity_id>/<int:student_question_id>/', GradeIndividualEssayView.as_view(), name='grade_individual_essay'),
    path('save_all_questions/<int:activity_id>/', SaveAllQuestionsView.as_view(), name='save_all_questions'),
    path('UpdateActivity/<int:activity_id>/', UpdateActivity, name='UpdateActivity'),
    path('retake_activity/<int:activity_id>/', RetakeActivityView.as_view(), name='retake_activity'),

    path('activity_completed/<int:score>/<int:activity_id>/<str:show_score>/', activityCompletedView, name='activity_completed'),
    path('activity_detail/<int:activity_id>/', ActivityDetailView.as_view(), name='activity_detail'),
    path('activityList/<int:subject_id>/', activityList, name='activityList'),
    path('toggleShowScore/<int:activity_id>/', toggleShowScore, name='toggleShowScore'),
    path('deleteActivity/<int:activity_id>/', deleteActivity, name='deleteActivity'),


    path('deleteActivityView/<int:activity_id>/', deleteActivityView, name='deleteActivityView'),

    path('activityTypeList/', activityTypeList, name='activityTypeList'),
    path('createActivityType/', createActivityType, name='createActivityType'),
    path('updateActivityType/<int:id>/', updateActivityType, name='updateActivityType'),
    path('deleteActivityType/<int:id>/', deleteActivityType, name='deleteActivityType'),

    path('participation_scores/<int:activity_id>/', participation_scores, name='participation_scores'),
    
]