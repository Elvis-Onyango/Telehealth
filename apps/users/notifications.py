# users/notifications.py
from pyfcm import FCMNotification
from django.conf import settings

push_service = FCMNotification(api_key=settings.FCM_DJANGO_SETTINGS['FCM_SERVER_KEY'])

def send_message_notification(user, message):
    # Get user's FCM registration IDs
    from fcm_django.models import FCMDevice
    devices = FCMDevice.objects.filter(user=user)
    
    if devices.exists():
        # Send notification
        result = push_service.notify_multiple_devices(
            registration_ids=list(devices.values_list('registration_id', flat=True)),
            message_title="New Message",
            message_body=f"You have a new message from {message.sender.get_full_name()}",
            data_message={
                "type": "new_message",
                "thread_id": str(message.thread.id),
                "message_id": str(message.id)
            }
        )
        return result
    return None