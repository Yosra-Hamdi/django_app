from django.db import models
from addresses.models import Address
from authentification.models import User
from customers.models import Customer
from products.models import Product
from stock.models import Stock






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
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Credit Card'),
    ]

    customer = models.ForeignKey("customers.Customer", related_name="orders", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_orders')  # Utilisateur qui gère la commande (administrateur, employé)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    creation_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNCONFIRMED')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='CASH')
    delivery_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='delivery_orders')
    billing_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='billing_orders')
    stock_preleve = models.BooleanField(default=False)


    def __str__(self):
        return f"Order #{self.id} - Status: {self.get_status_display()}"


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
        Calcule le montant total de la commande en tenant compte:
        - De la quantité de chaque produit
        - Du prix de vente (HT ou TTC selon include_vat)
        - De la TVA si le prix est HT
        """
        total = 0
        for order_product in self.products.all():
            product = order_product.product
            quantity = order_product.quantity
            
            if product.include_vat:
                # Si le prix est TTC, on l'utilise directement
                total += product.selling_price * quantity
            else:
                # Si le prix est HT, on ajoute la TVA
                total += (product.selling_price + product.vat_amount) * quantity
        
        self.total_amount = total
        self.save()
        return total

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"
    
