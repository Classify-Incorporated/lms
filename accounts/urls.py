from django.urls import path
from .views import (
    dashboard, activity_stream,
    assist, tools, sign_out, createProfile, user_login_view, admin_login_view,

    viewProfile, updateProfile, activateProfile, deactivateProfile, student
)

urlpatterns = [
    #Login Function
    path('', user_login_view, name='user_login_view'),
    path('admin_login_view/', admin_login_view, name='admin_login_view'),

    #View Profile
    path('student/', student, name='student'),
    path('viewProfile/<int:pk>/', viewProfile, name='viewProfile'),
    path('updateProfile/<int:pk>/', updateProfile, name='updateProfile'),
    path('activateProfile/<int:pk>/', activateProfile, name='activateProfile'),
    path('deactivateProfile/<int:pk>/', deactivateProfile, name='deactivateProfile'),
    

    path('dashboard/', dashboard, name='dashboard'),
    path('activity-stream/', activity_stream, name='activity_stream'),
    path('assist/', assist, name='assist'),
    path('tools/', tools, name='tools'),
    path('sign_out/', sign_out, name='sign_out'),
    path('createProfile/', createProfile, name='createProfile'),
]
