from django.urls import path
from .views import (
    AddActivityView, AddQuizTypeView, AddQuestionView, EditQuestionView, DisplayQuestionsView, 
    SubmitAnswersView, GradeEssayView, SaveAllQuestionsView,ActivityDetailView,
    activityCompletedView, studentQuizzesExams
)

urlpatterns = [
    path('add_activity/<int:subject_id>/', AddActivityView.as_view(), name='add_activity'),
    path('quiz_type/<int:activity_id>/', AddQuizTypeView.as_view(), name='add_quiz_type'),
    path('add_question/<int:activity_id>/<int:quiz_type_id>/', AddQuestionView.as_view(), name='add_question'),
    path('edit_question/<int:question_id>/', EditQuestionView.as_view(), name='edit_question'),
    path('display_question/<int:activity_id>/', DisplayQuestionsView.as_view(), name='display_question'),
    path('submit_answers/<int:activity_id>/', SubmitAnswersView.as_view(), name='submit_answers'),
    path('grade_essays/<int:activity_id>/', GradeEssayView.as_view(), name='grade_essays'),
    path('save_all_questions/<int:activity_id>/', SaveAllQuestionsView.as_view(), name='save_all_questions'),

    path('activity_completed/<int:score>/', activityCompletedView, name='activity_completed'),
    path('studentQuizzesExams/', studentQuizzesExams, name='studentQuizzesExams'),
    path('activity_detail/<int:activity_id>/', ActivityDetailView.as_view(), name='activity_detail'),
    
]