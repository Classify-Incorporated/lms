from django.urls import path
from .views import (
    dashboard, activity_stream, calendar,
    grades, assist, tools, sign_out, add_user, user_login_view, admin_login_view,

    viewProfile, editProfile, activateProfile, deactivateProfile, student
)

urlpatterns = [
    #Login Function
    path('', user_login_view, name='user_login_view'),
    path('admin_login_view/', admin_login_view, name='admin_login_view'),

    #View Profile
    path('student/', student, name='student'),
    path('viewProfile/<int:pk>/', viewProfile, name='viewProfile'),
    path('editProfile/<int:pk>/', editProfile, name='editProfile'),
    path('activateProfile/<int:pk>/', activateProfile, name='activateProfile'),
    path('deactivateProfile/<int:pk>/', deactivateProfile, name='deactivateProfile'),
    


    path('dashboard/', dashboard, name='dashboard'),
    path('activity-stream/', activity_stream, name='activity_stream'),
    path('calendar/', calendar, name='calendar'),
    path('grades/', grades, name='grades'),
    path('assist/', assist, name='assist'),
    path('tools/', tools, name='tools'),
    path('sign_out/', sign_out, name='sign_out'),
    path('add_user/', add_user, name='add_user'),
]
