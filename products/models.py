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
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField()
    image = models.ImageField(upload_to='produits/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.CharField(max_length=50, choices=UNIT_CHOICES, default='kilogram')

    def __str__(self):
        return self.name