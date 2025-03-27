
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, Notification
from .beams_config import beams_client

@receiver(post_save, sender=Order)
def envoyer_notification_commande(sender, instance, created, **kwargs):
    if created:  
        message = f"Une nouvelle commande a été passée : Commande #{instance.id}"

        # Envoyer via Pusher Beams
        try:
            beams_client.publish_to_interests(
                interests=['new_orders'],   
                publish_body={
                    'fcm': {
                        'notification': {
                            'title': 'Nouvelle commande',
                            'body': message,
                            'sound': 'default',
                        },
                        'data': {
                            'order_id': str(instance.id),  # Inclure l'ID de la commande
                            'action': 'open_order_details',  # Action pour rediriger
                        },
                    },
                },
            )
            print(f"Notification envoyée à l'utilisateur {instance.user.id}")
        except Exception as e:
            print(f"Erreur lors de l'envoi de la notification : {e}")

        # Enregistrer la notification en local
        Notification.objects.create(
            user=instance.user, 
            title='Nouvelle commande',
            body=message,
        )