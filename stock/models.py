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

    def update_stock(self, quantity):
        """Met à jour la quantité totale en stock."""
        self.quantity += quantity
        self.save()

    def reserve_stock(self, quantity):
        """Réserve une certaine quantité de stock."""
        if quantity <= self.quantity - self.reserved_quantity:
            self.reserved_quantity += quantity
            self.quantity -= quantity
            self.save()
            return True
        return False  # Si pas assez de stock disponible

    def unreserve_stock(self, quantity):
        """Libère une certaine quantité de stock réservé."""
        if quantity <= self.reserved_quantity:
            self.reserved_quantity -= quantity
            self.quantity += quantity
            self.save()
            return True
        return False  # Si pas assez de stock réservé

    def sell_stock(self, quantity):
        """Vente du stock réservé."""
        if quantity <= self.reserved_quantity:
            self.sold_quantity += quantity
            self.reserved_quantity -= quantity
            self.save()
            return True
        return False  # Si pas assez de stock réservé pour la vente

    def cancel_order(self, quantity):
        """Annule une commande et remet le stock initial."""
        self.quantity += quantity
        self.reserved_quantity -= quantity
        self.save()
