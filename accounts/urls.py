from django.urls import path
from .views import (
    dashboard, activity_stream,
    assist, tools, sign_out, createProfile, admin_login_view,

    viewProfile, updateProfile, activateProfile, deactivateProfile, student, staff_list, error,
    fetch_facebook_posts
)

urlpatterns = [
    #Login Function
    path('', admin_login_view, name='admin_login_view'),

    #View Profile
    path('student/', student, name='student'),
    path('staff_list/', staff_list, name='staff_list'),
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

    path('error/', error, name='error'),

    path('fetch_facebook_posts/', fetch_facebook_posts, name='fetch_facebook_posts'),
]
