from django.db import models
from django.utils import timezone
from .constants import PAYMENT_METHOD_CHOICES, PAYMENT_STATUS_CHOICES
from django.db.models.signals import post_save
from django.dispatch import receiver
from orders.models import Order 

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

    def update_status_based_on_order(self, force_save=False):
        """Met à jour le statut du paiement en fonction du statut de la commande"""
        if not hasattr(self, 'order') or self.order is None:
            return False
    
        original_status = self.status
        original_payment_date = self.payment_date
        original_refund_date = self.refund_date
    
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
    
    # Ne sauvegarder que si nécessaire et si demandé explicitement
        if force_save and (self.status != original_status or 
                        self.payment_date != original_payment_date or
                        self.refund_date != original_refund_date):
            self.save(update_fields=['status', 'payment_date', 'refund_date'])
            return True
        return False

def save(self, *args, **kwargs):
    """Surcharge de save pour la synchronisation automatique"""
    is_new = not self.pk
    
    if is_new and self.payment_method == 'CASH':
        self.status = 'PENDING'
    
    # Sauvegarde initiale sans déclencher update_status_based_on_order
    super().save(*args, **kwargs)
    
    # Après la sauvegarde, mise à jour si nécessaire (sans créer de récursion)
    if not is_new:
        self.update_status_based_on_order(force_save=True)

@receiver(post_save, sender=Order)
def update_related_payments(sender, instance, **kwargs):
    # Vérifie que c'est bien une sauvegarde normale (pas pendant la migration, etc.)
    if kwargs.get('raw', False):
        return
    
    # Met à jour tous les paiements liés
    for payment in instance.payments.all().only('id', 'status', 'payment_date', 'refund_date'):
        try:
            payment.update_status_based_on_order(force_save=True)
        except Exception as e:
            logger.error(f"Error updating payment {payment.id}: {str(e)}")