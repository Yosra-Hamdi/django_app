from django.db import models
from products.models import Product

class Stock(models.Model):
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='stock'
    )
    quantity = models.PositiveIntegerField(default=0)  # Quantité en stock
    reserved_quantity = models.PositiveIntegerField(default=0)  # Quantité réservée
    sold_quantity = models.PositiveIntegerField(default=0)  # Quantité vendue
    last_updated = models.DateTimeField(auto_now=True)  # Date de dernière mise à jour

    def __str__(self):
        return f"Stock de {self.product.name} : Total={self.quantity}, Réservé={self.reserved_quantity}, Vendu={self.sold_quantity}"
   