# orders/models.py

from company.models import CompanyInfo
from orders.models import Order
from django.utils import timezone 
from django.db import models


class DeliveryNote(models.Model):
    """
    Modèle pour les bons de livraison
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='delivery_notes')
    delivery_date = models.DateField(default=timezone.now)
    reference = models.CharField(max_length=50, unique=True)
    is_delivered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bon de Livraison"
        verbose_name_plural = "Bons de Livraison"
        ordering = ['-delivery_date']

    def __str__(self):
        return f"BL-{self.reference}"

    def generate_reference(self):
        """Génère une référence unique pour le bon de livraison"""
        date_part = timezone.now().strftime('%Y%m%d')
        # Utilisez le pk si l'id n'est pas encore disponible
        obj_id = self.pk or "temp"
        return f"BL-{date_part}-{obj_id:04}"

    def save(self, *args, **kwargs):
        if not self.reference:
         # Sauvegardez d'abord pour obtenir un ID
            super().save(*args, **kwargs)
            self.reference = self.generate_reference()
            # Sauvegardez à nouveau avec la référence
            kwargs['force_insert'] = False
        super().save(*args, **kwargs)

    @property
    def customer_info(self):
        """Retourne les infos du client"""
        return {
            'full_name': f"{self.order.customer.first_name} {self.order.customer.last_name}",
            'address': str(self.order.delivery_address),
            'phone': self.order.customer.phone
        }

    @property
    def products_info(self):
        """Retourne la liste des produits avec leurs infos"""
        return [{
            'name': item.product.name,
            'quantity': item.quantity,
            'unit_price': float(item.unit_price_ht),
            'total': float(item.total_ttc)
        } for item in self.order.products.all()]

    @property
    def payment_info(self):
        """Retourne les infos de paiement"""
        return {
            'method': self.order.get_payment_method_display(),
            'subtotal': float(self.order.subtotal_ht),
            'vat': float(self.order.total_vat),
            'total': float(self.order.total_ttc)
        }

    def mark_as_delivered(self):
        """Marque le bon comme livré"""
        self.is_delivered = True
        self.save()
        self.order.status = 'DELIVERED_PAID'
        self.order.save()
    
    @property
    def company_info(self):
        """Retourne les informations de l'entreprise"""
        company = CompanyInfo.objects.first()
        if not company:
            return {
                'name': '',
                'address': '',
                'phone': '',
                'email': ''
            }
        return {
            'name': company.name,
            'address': str(company.address),
            'phone': company.phone,
            'email': company.email
        }