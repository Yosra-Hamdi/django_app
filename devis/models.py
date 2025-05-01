from decimal import Decimal
from django.db import models

# Create your models here.
from django.db import models
from products.models import Product
from customers.models import Customer

class Devis(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Brouillon'),
        ('SENT', 'Envoyé'),
        ('ACCEPTED', 'Accepté'),
        ('REJECTED', 'Refusé'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='devis')
    reference = models.CharField(max_length=50, unique=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_validite = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    notes = models.TextField(blank=True)
    remise = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Remise en %

    def __str__(self):
        return f"Devis {self.reference} - {self.customer}"

    @property
    def total_ht(self):
        return sum(Decimal(str(item.montant_ht)) for item in self.lignes.all())

    @property
    def total_tva(self):
        return sum(Decimal(str(item.montant_tva)) for item in self.lignes.all())

    @property
    def total_ttc(self):
        total_ht = Decimal(str(self.total_ht))
        remise = Decimal(str(self.remise))
        total_tva = Decimal(str(self.total_tva))
        return total_ht * (Decimal('1') - remise / Decimal('100')) + total_tva

class LigneDevis(models.Model):
    devis = models.ForeignKey(Devis, on_delete=models.CASCADE, related_name='lignes')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=False)
    quantite = models.PositiveIntegerField() 
    prix_unitaire_ht = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True,  # Rendre le champ nullable
        blank=True
    )

    tva = models.DecimalField(max_digits=5, decimal_places=2)  # TVA en %

    @property
    def prix_unitaire_effectif(self):
        if self.prix_unitaire_ht is not None:
            return Decimal(str(self.prix_unitaire_ht))
        return Decimal(str(self.product.selling_price))

    @property
    def montant_ht(self):
        return Decimal(str(self.quantite)) * self.prix_unitaire_effectif

    @property
    def montant_tva(self):
        return self.montant_ht * (Decimal(str(self.tva)) / Decimal('100'))
    def __str__(self):
        return f"{self.product.name} x{self.quantite}"