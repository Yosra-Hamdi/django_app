from django.db import models
from company.models import CompanyInfo
from orders.models import Order
from customers.models import Customer
from payments.constants import PAYMENT_METHOD_CHOICES
from products.models import Product
from addresses.models import Address
from django.utils import timezone
from django.core.validators import MinValueValidator

class Invoice(models.Model):
    # Pour les factures liées à une commande
    order = models.OneToOneField(
        Order, 
        on_delete=models.CASCADE, 
        related_name='invoice',
        null=True,
        blank=True
    )
    
    # Pour les factures manuelles
    invoice_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    
    # Informations client (peuvent venir de la commande ou être saisis manuellement)
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    billing_address = models.ForeignKey(
        Address, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='invoice_billing_address'
    )
    delivery_address = models.ForeignKey(
        Address, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='invoice_delivery_address'
    )
    
    # Méthodes de paiement et livraison
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHOD_CHOICES, 
        default='CASH'
    )
    delivery_method = models.CharField(
        max_length=20, 
        choices=Order.DELIVERY_METHOD_CHOICES, 
        default='DELIVERY'
    )
    
    # Totaux
    subtotal_ht = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    total_vat = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    total_ttc = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    
   
    
    notes = models.TextField(blank=True, null=True)

    def generate_invoice_number(self):
        date_part = timezone.now().strftime('%Y%m')
        return f"FACT-{date_part}-{self.id:05d}"

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating and not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
            super().save(update_fields=['invoice_number'])
    
    def calculate_totals(self):
        """Calcule les totaux à partir des lignes de facture"""
        self.subtotal_ht = sum(item.total_ht for item in self.items.all())
        self.total_vat = sum(item.vat_amount for item in self.items.all())
        self.total_ttc = self.subtotal_ht + self.total_vat
        self.save()

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

 
class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.SET_NULL, 
        null=True
    )
    
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    unit_price_ht = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    vat_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
          null=True,  # Rendre le champ nullable
        blank=True
    )
    
    @property
    def total_ht(self):
        return self.unit_price_ht * self.quantity
        
    @property
    def vat_amount(self):
        return self.total_ht * (self.vat_rate / 100)
        
    @property
    def total_ttc(self):
        return self.total_ht + self.vat_amount
    
    def save(self, *args, **kwargs):
        # Si c'est un produit, remplir automatiquement description, prix et TVA
        if self.product:
           
            if not self.unit_price_ht:
                self.unit_price_ht = self.product.price_excluding_vat
            if not self.vat_rate:
                self.vat_rate = self.product.vat_rate
        
        # Valeurs par défaut si tout est vide
        if not self.unit_price_ht:
            self.unit_price_ht = 0
        if not self.vat_rate:
            self.vat_rate = 0
        
        super().save(*args, **kwargs)
        self.invoice.calculate_totals()