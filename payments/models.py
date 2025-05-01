from django.db import models
from django.utils import timezone
from .constants import PAYMENT_METHOD_CHOICES, PAYMENT_STATUS_CHOICES

class Payment(models.Model):
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="payments")
    
    # Informations paiement
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES , default='CASH')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    refund_date = models.DateTimeField(null=True, blank=True)



    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'

    def update_status_based_on_order(self):
        """Met à jour le statut du paiement en fonction du statut de la commande"""
        if self.order.status in ['PAID', 'DELIVERED_PAID']:
            self.status = 'PAID'
            if not self.payment_date:
                self.payment_date = timezone.now()
        elif self.order.status == 'CANCELLED':
            self.status = 'PENDING'
        elif self.order.status == 'RETURNED':
            self.status = 'REFUNDED'
            if not self.refund_date:
                self.refund_date = timezone.now()
        elif self.order.status == 'PAYMENT_ERROR':
            self.status = 'FAILED'
        # Pour les autres statuts, on ne change pas le statut du paiement
        
        self.save()

    def save(self, *args, **kwargs):
        """Surcharge de save pour la synchronisation automatique"""
        is_new = not self.pk
    
        # Pour un nouveau paiement en espèces, on met PENDING au lieu de PAID
        if is_new and self.payment_method == 'CASH':
            self.status = 'PENDING'  # Changé de 'PAID' à 'PENDING'
    
        super().save(*args, **kwargs)
    
        # Pour les paiements existants, on met à jour selon le statut de la commande
        if not is_new:
            self.update_status_based_on_order()