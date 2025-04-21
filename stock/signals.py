from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from orders.models import Order
from products.models import Product
from django.db.models.signals import pre_save

from .models import Stock

# Signal pour détecter les changements d'état
@receiver(pre_save, sender=Order)
def handle_order_status_change(sender, instance, **kwargs):
    if not instance.pk:  # Nouvelle commande, pas de changement d'état
        return
    
    try:
        old_order = Order.objects.get(pk=instance.pk)
        if old_order.status != instance.status:
            instance.update_stock_on_status_change(old_order.status, instance.status)
    except Order.DoesNotExist:
        pass