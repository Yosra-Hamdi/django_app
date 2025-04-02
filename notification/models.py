from django.db import models

from orders.models import Order

# Create your models here.
class Notification(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(Order,on_delete=models.SET_NULL, null=True,blank=True,
         )
    def __str__(self):
        return f"{self.title} - {self.created_at}"