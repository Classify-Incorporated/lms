# urls.py
from django.urls import path
from .views import (send_message, inbox, view_message, unread_count ,check_authentication,sent
                    ,trash,trash_messages,untrash_messages,view_sent_message,reply_message,
                    view_trash_message, send_test_email
)
urlpatterns = [
    path('send_message/', send_message, name='send_message'),
    path('inbox/', inbox, name='inbox'),
    path('sent/', sent, name='sent'),
    path('trash/', trash, name='trash'),
    path('message/<int:message_id>/', view_message, name='view_message'),
    path('message/sent/<int:message_id>/', view_sent_message, name='view_sent_message'),
    path('message/trash/<int:message_id>/', view_trash_message, name='view_trash_message'),
    path('unread_count/', unread_count, name='unread_count'),
     path('trash_messages/', trash_messages, name='trash_messages'),
     path('untrash_messages/', untrash_messages, name='untrash_messages'),
    path('check_authentication/', check_authentication, name='check_authentication'),
    
    # New URL pattern for replying to messages
    path('message/<int:message_id>/reply/', reply_message, name='reply_message'),
    path('send_test_email/', send_test_email, name='send_test_email'),
]
