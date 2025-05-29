from django.db.models.signals import post_save
from django.dispatch import receiver
from notification.models import Notification
from .models import Order
from project.soketi_client import send_soketi_event
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Order)
def envoyer_notification_commande(sender, instance, created, **kwargs):
    if not created:
        return

    message = f"Nouvelle commande #{instance.id}"

    try:
        # Envoi à Soketi
        send_soketi_event(
            channel='new-orders',
            event_name='new-order-event',
            data={
                'order_id': instance.id,
                'message': message
            }
        )

        # Notification DB (facultatif)
        Notification.objects.create(
            title='Nouvelle commande',
            body=message,
            order_id=instance.id
        )

    except Exception as e:
        logger.error(f"Erreur d'envoi de notification : {str(e)}")
