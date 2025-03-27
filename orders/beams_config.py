
from pusher_push_notifications import PushNotifications
from django.conf import settings

beams_client = PushNotifications(
    instance_id=settings.PUSHER_BEAMS_INSTANCE_ID,
    secret_key=settings.PUSHER_BEAMS_SECRET_KEY,
)