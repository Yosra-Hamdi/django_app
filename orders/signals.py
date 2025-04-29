from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from notification.models import Notification
from .models import Order

from .beams_config import beams_client
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Order)
def envoyer_notification_commande(sender, instance, created, **kwargs):
    if not created:
        return

    message = f"nouvelle commande a été passée #{instance.id}"
    
    try:
       
        response = beams_client.publish_to_interests(
            interests=['new_orders'], 
            publish_body={
                'web': {
                    'notification': {
                        'title': 'Nouvelle commande',
                        'body': message,
                        
                    },
                    'data': {
                        'type': 'new_order',
                        'order_id': str(instance.id),
                       
                    }
                },
                'fcm': {
                    'notification': {
                        'title': 'Nouvelle commande',
                        'body': message,
                        'sound': 'default'
                    },
                    'data': {
                        'order_id': str(instance.id),
                        'action': 'open_order_details'
                    }
                }
            }
        )
        logger.info(f"Notification envoyée à new_orders. ID: {response['publishId']}")
        
        Notification.objects.create(
            
            title='Nouvelle commande',
            body=message,
            order_id=str(instance.id)

        )

    except Exception as e:
        logger.error(f"Échec d'envoi à new_orders: {str(e)}", exc_info=True)