from django.db import models
from addresses.models import Address
from authentification.models import User
from customers.models import Customer
from payments.constants import PAYMENT_METHOD_CHOICES
from products.models import Product
from stock.models import Stock
from django.utils import timezone 





class Order(models.Model):
    STATUS_CHOICES = [
        ('UNCONFIRMED', 'Commande non confirmée'),
        ('CONFIRMED', 'Commande confirmée'),
    
        ('STOCK_VERIFICATION', 'Vérification du stock'),
        ('PREPARATION', 'Préparation de la commande'),
        ('PACKAGING', 'Emballage de la commande'),

        ('WAITING_FOR_PAYMENT', 'En attente de paiement'),
        ('PAYMENT_ERROR', 'Erreur de paiement'),
        ('PAID', 'Payée'),
    
        ('SHIPPED', 'Commande expédiée'),
        ('DELIVERED_PAID', 'Commande livrée et payée'),
    
        ('CANCELLED', 'Annulée'),
        ('RETURNED', 'Retournée'),
    ]
   

    customer = models.ForeignKey("customers.Customer", related_name="orders", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_orders')  # Utilisateur qui gère la commande (administrateur, employé)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    creation_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNCONFIRMED')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES , default='CASH')
    delivery_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='delivery_orders')
    billing_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='billing_orders')
    stock_preleve = models.BooleanField(default=False)
    subtotal_ht = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_vat = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=10, decimal_places=2, default=0)


    def __str__(self):
        return f"Order #{self.id} - Status: {self.get_status_display()}"
    

    def create_payment(self):
        """Crée le paiement associé avec statut approprié"""
        payment = self.payments.create(
            amount=self.total_ttc,
            payment_method=self.payment_method,
            status='PAID' if self.payment_method == 'CASH' else 'PENDING'
        )
        return payment
    
    def calculate_totals(self):
        """Calcule tous les montants et les sauvegarde"""
        self.subtotal_ht = sum(item.total_ht for item in self.products.all())
        self.total_vat = sum(item.vat_amount for item in self.products.all())
        self.total_ttc = self.subtotal_ht + self.total_vat
        self.total_amount = self.total_ttc  # Pour compatibilité
        self.save()
    
    def generate_order_number(self):
        date_part = timezone.now().strftime('%Y%m%d')  # Maintenant correct
        return f"CMD-{date_part}-{self.id:04d}"


    def update_stock_on_status_change(self, old_status, new_status):
        """Met à jour le stock selon les règles spécifiées"""
        
        # États qui déclenchent le prélèvement initial du stock
        etats_prelevement = {
            'CONFIRMED', 'STOCK_VERIFICATION', 'PREPARATION',
            'PACKAGING', 'WAITING_FOR_PAYMENT', 'PAYMENT_ERROR',
            'SHIPPED'
        }
        
        # 1. Prélèvement initial du stock
        if (old_status == 'UNCONFIRMED' and 
            new_status in etats_prelevement and 
            not self.stock_preleve):
            
            for item in self.products.all():
                try:
                    stock = Stock.objects.get(product=item.product)
                    if stock.quantity >= item.quantity:
                        stock.quantity -= item.quantity
                        stock.reserved_quantity += item.quantity
                        stock.save()
                    else:
                        raise ValueError(f"Stock insuffisant pour {item.product.name}")
                except Stock.DoesNotExist:
                    raise ValueError(f"Stock non trouvé pour {item.product.name}")
            
            self.stock_preleve = True
            self.save()
        
        # 2. Commande payée ou livrée - transfert vers vendu
        elif new_status in ['PAID', 'DELIVERED_PAID'] and self.stock_preleve:
            for item in self.products.all():
                try:
                    stock = Stock.objects.get(product=item.product)
                    if stock.reserved_quantity >= item.quantity:
                        stock.reserved_quantity -= item.quantity
                        stock.sold_quantity += item.quantity
                        stock.save()
                except Stock.DoesNotExist:
                    pass
        
        # 3. Commande annulée/retournée - restitution du stock
        elif new_status in ['CANCELLED', 'RETURNED'] and self.stock_preleve:
            for item in self.products.all():
                try:
                    stock = Stock.objects.get(product=item.product)
                    stock.quantity += item.quantity
                    stock.reserved_quantity -= item.quantity
                    stock.save()
                except Stock.DoesNotExist:
                    pass
            
            self.stock_preleve = False
            self.save()

















    def calculate_total(self):
        """
        Calcule le montant total TTC de la commande en utilisant les prix
        sauvegardés dans OrderProduct
        """
        self.total_amount = sum(item.total_ttc for item in self.products.all())
        self.save()
        return self.total_amount

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price_ht = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Prix unitaire HT
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2 , null=True, blank=True )  # Taux de TVA
    

    def save(self, *args, **kwargs):
        # S'assurer que unit_price_ht et vat_rate sont remplis à la création
        if not self.pk:  # Si c'est une nouvelle instance
            self.unit_price_ht = self.product.price_excluding_vat
            self.vat_rate = self.product.vat_rate
        super().save(*args, **kwargs)

        
    @property
    def total_ht(self):
        return self.unit_price_ht * self.quantity
        
    @property
    def vat_amount(self):
        return self.total_ht * (self.vat_rate / 100)
        
    @property
    def total_ttc(self):
        return self.total_ht + self.vat_amount
    
