from django.db import models

# Create your models here.
from django.utils import timezone

class DailySales(models.Model):
    date = models.DateField(unique=True)
    total_orders = models.PositiveIntegerField()
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = "Statistique quotidienne"
        verbose_name_plural = "Statistiques quotidiennes"
        ordering = ['-date']

    def __str__(self):
        return f"Stats du {self.date}"