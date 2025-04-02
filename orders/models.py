from django.db import models
from addresses.models import Address
from authentification.models import User
from customers.models import Customer
from products.models import Product






class Order(models.Model):
    STATUS_CHOICES = [
        ('UNCONFIRMED', 'Unconfirmed'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('PAID', 'Paid'),
        ('DELIVERED', 'Delivered'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Credit Card'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_orders')  # Utilisateur qui gère la commande (administrateur, employé)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    creation_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNCONFIRMED')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='CASH')
    delivery_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='delivery_orders')
    billing_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='billing_orders')


    def __str__(self):
        return f"Order #{self.id} - Status: {self.get_status_display()}"

    def calculate_total(self):
        total = sum([cp.product.price * cp.quantity for cp in self.products.all()])
        self.total_amount = total
        self.save()
        return total

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"
    
