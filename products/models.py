from django.db import models

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
class Product(models.Model):
    UNIT_CHOICES = [
        ('kg','kilogram'),
        ('Liter', 'liter'),
        ('Meter', 'meter'),
    ]
    name = models.CharField(max_length=100)
    stock_quantity = models.PositiveIntegerField()
    image = models.ImageField(upload_to='produits/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.CharField(max_length=50, choices=UNIT_CHOICES, default='kilogram')
    purchase_price  = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name="Coût d'achat")
    selling_price = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name="Prix de vente unitaire")
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="TVA (%)")
    include_vat = models.BooleanField(default=False, verbose_name="Toutes taxes comprises (TTC)")


    def __str__(self):
        return self.name
    
    @property
    def vat_amount(self):
        """Calcule le montant de la TVA"""
        return self.selling_price * self.vat_rate / 100
    

    @property
    def price_excluding_vat(self):
        """Prix hors taxe (HT)"""
        if self.include_vat:
            return self.selling_price / (1 + self.vat_rate / 100)
        return self.selling_price
    
    @property
    def price_including_vat(self):
        """Prix toutes taxes comprises (TTC)"""
        if not self.include_vat:
            return self.selling_price * (1 + self.vat_rate / 100)
        return self.selling_price
    