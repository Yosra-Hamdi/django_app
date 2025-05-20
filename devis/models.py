from decimal import Decimal
from django.db import models

# Create your models here.
from company.models import CompanyInfo
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



    @property
    def company_info(self):
        """Retourne les infos de l'entreprise sous forme de dictionnaire"""
        company = CompanyInfo.objects.first()
        if not company:
            return {
                'name': '',
                'address': '',
                'phone': '',
                'email': '',
                'logo': ''
            }
        return {
            'name': company.name,
            'address': str(company.address) if company.address else '',
            'phone': company.phone,
            'email': company.email,
            'logo': company.logo.url if company.logo else ''
        }
class LigneDevis(models.Model):
    devis = models.ForeignKey(Devis, on_delete=models.CASCADE, related_name='lignes')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True, default="")
    quantite = models.PositiveIntegerField(default=1)
    prix_unitaire_ht = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tva = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = "Ligne de devis"
        verbose_name_plural = "Lignes de devis"

    @property
    def montant_ht(self):
        if self.prix_unitaire_ht is not None:
            return Decimal(str(self.quantite)) * self.prix_unitaire_ht
        elif self.product:
            return Decimal(str(self.quantite)) * self.product.selling_price
        return Decimal('0')

    @property
    def montant_tva(self):
        return self.montant_ht * (Decimal(str(self.tva)) / Decimal('100'))

    def __str__(self):
        if self.product:
            return f"{self.product.name} x{self.quantite} (HT: {self.montant_ht:.2f} TND)"
        return f"{self.description} x{self.quantite}" if self.description else f"Ligne #{self.id}"