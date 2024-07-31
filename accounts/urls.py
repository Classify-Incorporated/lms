from django.urls import path
from .views import (
    dashboard, student, activity_stream, courses, calendar,
    messages, grades, assist, tools, sign_out, login, add_user
)

urlpatterns = [
    path('', login, name='login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('student/', student, name='student'),
    path('activity-stream/', activity_stream, name='activity_stream'),
    path('courses/', courses, name='courses'),
    path('calendar/', calendar, name='calendar'),
    path('messages/', messages, name='messages'),
    path('grades/', grades, name='grades'),
    path('assist/', assist, name='assist'),
    path('tools/', tools, name='tools'),
    path('sign-out/', sign_out, name='sign_out'),
    path('add_user/', add_user, name='add_user'),
]
