from .models import MessageUnreadStatus
from accounts.models import Profile, CustomUser

def unread_messages_count(request):
    if not request.user.is_authenticated:
        return {'unread_messages_count': 0}

    try:
        # Fetch user using email
        user = CustomUser.objects.get(email=request.user.email)
        user_id = user.id
    except CustomUser.DoesNotExist:
        user_id = None

    unread_count = 0
    if user_id:
        unread_count = MessageUnreadStatus.objects.filter(user_id=user_id).count()
    
    return {'unread_messages_count': unread_count}
