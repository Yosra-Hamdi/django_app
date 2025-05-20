from django.db import models
from django.db.models import Sum, F

from authentification.models import User
from categories.models import Category
# Create your models here.

class Product(models.Model):
    UNIT_CHOICES = [
        ('kg','kilogram'),
        ('Liter', 'liter'),
        ('Meter', 'meter'),
        
    ]
    name = models.CharField(max_length=100)
    barcode = models.CharField(max_length=50, unique=True, null=True, blank=True) # 
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True , related_name='products')
    unit = models.CharField(max_length=50, choices=UNIT_CHOICES, default='kg')
    purchase_price  = models.DecimalField(max_digits=10, decimal_places=3,  verbose_name="Coût d'achat")
    selling_price = models.DecimalField(max_digits=10, decimal_places=3,  verbose_name="Prix de vente unitaire")
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="TVA (%)")
    include_vat = models.BooleanField(default=False, verbose_name="Toutes taxes comprises (TTC)")
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name
    
    @property
    def vat_amount(self):
        """Calcule le montant de la TVA"""
        if self.include_vat:
         # Si le prix est TTC, on calcule la TVA à partir du HT
            ht_price = self.price_excluding_vat
            return ht_price * (self.vat_rate / 100)
        else:
        # Si le prix est HT, calcul direct
            return self.selling_price * (self.vat_rate / 100)

    @property
    def price_excluding_vat(self):
        """Prix hors taxe (HT)"""
        if self.include_vat:
            return (self.selling_price) / (1 + (self.vat_rate) / 100)
        return (self.selling_price)
    
    @property
    def price_including_vat(self):
        """Prix toutes taxes comprises (TTC)"""
        if self.include_vat:
            return self.selling_price
        else:
            return self.selling_price * (1 + self.vat_rate / 100)


    @property
    def main_image(self):
        """Retourne l'image principale ou la première image disponible"""
        main_img = self.product_images.filter(is_primary=True).first()
        if main_img:
            return main_img.gallery_image
        first_img = self.product_images.first()
        return first_img.gallery_image if first_img else None

    @property
    def total_units_sold(self):
        """Retourne le nombre total d'unités vendues"""
        return self.orderproduct_set.aggregate(
            total=Sum('quantity')
        )['total'] or 0

    @property
    def total_revenue(self):
        """Retourne le chiffre d'affaires généré par le produit"""
        return self.orderproduct_set.aggregate(
            revenue=Sum(F('quantity') * F('unit_price_ht'))
        )['revenue'] or 0

    @classmethod
    def create_quick_product(cls, name, selling_price, vat_rate=0, unit='kg'):
        """Méthode helper pour créer un produit rapidement"""
        return cls.objects.create(
            name=name,
            selling_price=selling_price,
            vat_rate=vat_rate,
            unit=unit,
            purchase_price=0,
            include_vat=False
        )





class ProductHistory(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Création'),
        ('UPDATE', 'Modification'),
        ('DELETE', 'Suppression'),
        ('STOCK_ADD', 'Ajout stock'),
        ('STOCK_REMOVE', 'Retrait stock'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    changed_fields = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.get_action_display()} par {self.user}"

