from .models import Notification, ChatMessage


def notification_context(request):
    unread_notifications_count = 0
    unread_messages_count = 0

    if request.user.is_authenticated:
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
        unread_messages_count = ChatMessage.objects.filter(receiver=request.user, is_read=False).count()

    return {
        'unread_notifications_count': unread_notifications_count,
        'unread_messages_count': unread_messages_count,
    }