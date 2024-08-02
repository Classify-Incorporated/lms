# urls.py
from django.urls import path
from .views import send_message, message, view_message, unread_count ,check_authentication

urlpatterns = [
    path('send_message/', send_message, name='send_message'),
    path('message/', message, name='message'),
    path('message/<int:message_id>/', view_message, name='view_message'),
    path('unread_count/', unread_count, name='unread_count'),

    path('check_authentication/', check_authentication, name='check_authentication'),
]
