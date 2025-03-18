from django.db import models

from addresses.models import Address

# Create your models here.
class Customer(models.Model):
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100, default="Unknown")
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.ForeignKey( Address ,on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"