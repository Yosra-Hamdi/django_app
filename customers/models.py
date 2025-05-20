from django.utils import timezone

from django.db import models
from addresses.models import Address

# Create your models here.
class Customer(models.Model):
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100, default="Unknown")
    email = models.EmailField(unique=False, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.ForeignKey( Address ,on_delete=models.SET_NULL, null=True,blank=True)
    date_joined = models.DateTimeField(default=timezone.now)  # Ajoutez ce champ

    def __str__(self):
        return f"{self.first_name} {self.last_name}"