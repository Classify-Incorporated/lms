from django.urls import path
from .views import (
    AddActivityView, AddQuizTypeView, AddQuestionView, EditQuestionView, DisplayQuestionsView, SubmitAnswersView, GradeEssayView, 
    activityCompletedView, studentQuizzesExams
)

urlpatterns = [
    path('add_activity/<int:subject_id>/', AddActivityView.as_view(), name='add_activity'),
    path('quiz_type/<int:activity_id>/', AddQuizTypeView.as_view(), name='add_quiz_type'),
    path('question/<int:activity_id>/<int:quiz_type_id>/', AddQuestionView.as_view(), name='add_question'),
    path('edit_question/<int:question_id>/', EditQuestionView.as_view(), name='edit_question'),
    path('display_question/<int:activity_id>/', DisplayQuestionsView.as_view(), name='display_question'),
    path('submit_answers/<int:activity_id>/', SubmitAnswersView.as_view(), name='submit_answers'),
    path('grade_essays/<int:activity_id>/', GradeEssayView.as_view(), name='grade_essays'),

    path('activity_completed/<int:score>/', activityCompletedView, name='activity_completed'),
    path('studentQuizzesExams/', studentQuizzesExams, name='studentQuizzesExams'),
    
]