from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from orders.models import Order
from products.models import Product

from .models import Stock

@receiver(post_save, sender=Product)
def create_product_stock(sender, instance, created, **kwargs):
    if created:
        Stock.objects.create(product=instance, quantity=0)  # Quantité initiale à 0

@receiver(post_save, sender=Order)
def update_stock_on_order_change(sender, instance, created, **kwargs):
    """Mise à jour du stock en fonction de l'état de la commande."""
    if instance.status == 'CONFIRMED':
        # Réserver le stock pour les produits de la commande
        for order_product in instance.products.all():
            stock = order_product.product.stock
            stock.reserve_stock(order_product.quantity)
    elif instance.status == 'PAID' or instance.status == 'DELIVERED':
        # Marquer les produits comme vendus
        for order_product in instance.products.all():
            stock = order_product.product.stock
            stock.sell_stock(order_product.quantity)
    elif instance.status == 'CANCELLED':
        # Réinitialiser le stock si la commande est annulée
        for order_product in instance.products.all():
            stock = order_product.product.stock
            stock.cancel_order(order_product.quantity)

@receiver(post_delete, sender=Order)
def update_stock_on_order_delete(sender, instance, **kwargs):
    """Mise à jour du stock lorsque la commande est supprimée."""
    if instance.status == 'CONFIRMED':
        # Libérer le stock réservé si la commande est supprimée
        for order_product in instance.products.all():
            stock = order_product.product.stock
            stock.unreserve_stock(order_product.quantity)
