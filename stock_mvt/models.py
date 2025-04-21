from django.db import models
from django.conf import settings
from stock.models import Stock

class StockMovement(models.Model):
    REASONS = [
        ('SOLD', 'Vendu'),
        ('RETURN', 'Retour'),
        ('DAMAGED', 'Endommagé'),
        ('WITHDRAWAL', 'Prélèvement'),
        ('RESTOCK', 'Réapprovisionnement')
    ]
     
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='movements')
    quantity = models.IntegerField()
    reason = models.CharField(max_length=50, choices=REASONS)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements'
    )
    
    def __str__(self):
        return f"Mouvement de stock: {self.quantity} ({self.get_reason_display()}) par {self.user}"
    


    def save(self, *args, **kwargs):
        # 1. Utilisateur défini explicitement
        if not hasattr(self, '_current_user'):
            # 2. Récupération depuis le contexte
            request = getattr(self, '_request', None)
            if request and hasattr(request, 'user'):
                self._current_user = request.user
        
        # Définir l'utilisateur si absent
        if not self.user_id and hasattr(self, '_current_user'):
            self.user = self._current_user
        
        super().save(*args, **kwargs)