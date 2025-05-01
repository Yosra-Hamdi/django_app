from django.db import models
from addresses.models import Address

class CompanyInfo(models.Model):
    name = models.CharField(max_length=255)
    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        db_column='address_id'  # Ajoutez cette ligne
    )
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    logo = models.ImageField(upload_to='company/', null=True, blank=True)

    def __str__(self):
        return self.name