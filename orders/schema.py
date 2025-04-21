from graphene_django import DjangoObjectType
import graphene
from graphene import Decimal, Enum
from addresses.schema import AddressType
from authentification.models import User
from customers.models import Customer
from products.models import Product
from addresses.models import Address
from .models import  Order, OrderProduct
from graphql import GraphQLError
from .beams_config import beams_client



# Enum pour les statuts de la commande
class StatusEnum(graphene.Enum):
    UNCONFIRMED = "UNCONFIRMED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    PAID = "PAID"
    RETURNED = "RETURNED"
    DELIVERED_PAID = "DELIVERED_PAID"
    STOCK_VERIFICATION = "STOCK_VERIFICATION"
    PREPARATION = "PREPARATION"
    PACKAGING = "PACKAGING"
    WAITING_FOR_PAYMENT = "WAITING_FOR_PAYMENT"
    PAYMENT_ERROR = "PAYMENT_ERROR"
    SHIPPED = "SHIPPED"

# Enum pour les méthodes de paiement
class PaymentMethodEnum(Enum):
    CASH = "CASH"
    CARD = "CARD"

# Type GraphQL pour OrderProduct
class OrderProductType(DjangoObjectType):
    class Meta:
        model = OrderProduct
        fields = ("id", "product", "quantity")

# Type GraphQL pour Order
class OrderType(DjangoObjectType):
    total_amount = graphene.Float()
    total_amount_with_tax = graphene.Float()
    total_tax_amount = graphene.Float()

    class Meta:
        model = Order
        fields = ("id", "products", "customer", "total_amount", "status", "creation_date", "payment_method", "delivery_address", "billing_address")

    # Calcul du montant total
    def resolve_total_amount(self, info):
        """Retourne le montant HT si include_vat=False, sinon retourne le montant TTC"""
        return float(self.calculate_total())

    def resolve_total_amount_with_tax(self, info):
        """Retourne toujours le montant TTC"""
        total = Decimal('0')
        for order_product in self.products.all():
            product = order_product.product
            quantity = order_product.quantity
            total += (product.selling_price + product.vat_amount) * quantity
        return float(total)

    def resolve_total_tax_amount(self, info):
        """Retourne le montant total de la TVA"""
        total_tax = Decimal('0')
        for order_product in self.products.all():
            product = order_product.product
            quantity = order_product.quantity
            if not product.include_vat:  # Si prix HT, on ajoute la TVA
                total_tax += product.vat_amount * quantity
        return float(total_tax)


# Requêtes GraphQL
class Query(graphene.ObjectType):
    orders = graphene.List(OrderType)
    order = graphene.Field(OrderType, id=graphene.ID(required=True))
   

    def resolve_orders(root, info):
        return Order.objects.all()

    def resolve_order(root, info, id):
        try:
            return Order.objects.get(pk=id)
        except Order.DoesNotExist:
            raise GraphQLError("Commande non trouvée.")
        
   

   
# Input pour les produits
class ProductInput(graphene.InputObjectType):
    product_id = graphene.ID(required=True)
    quantity = graphene.Int(required=True)

# Mutation pour mettre à jour une commande
class UpdateOrder(graphene.Mutation):
    class Arguments:
        order_id = graphene.ID(required=True)
        products = graphene.List(ProductInput, required=True)
        billing_address_id = graphene.ID(required=False)

    order = graphene.Field(OrderType)

    def mutate(self, info, order_id, products, billing_address_id=None):
        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            raise GraphQLError("Commande non trouvée.")

        if billing_address_id:
            try:
                billing_address = Address.objects.get(pk=billing_address_id)
                order.billing_address = billing_address
            except Address.DoesNotExist:
                raise GraphQLError("Adresse de facturation non trouvée.")

        # Supprimer les produits existants de la commande
        order.products.all().delete()

        # Ajouter les nouveaux produits
        for item in products:
            try:
                product = Product.objects.get(pk=item.product_id)
            except Product.DoesNotExist:
                raise GraphQLError(f"Produit avec l'ID {item.product_id} non trouvé.")

            quantity = item.quantity
            if quantity <= 0:
                raise GraphQLError("La quantité doit être supérieure à zéro.")

            OrderProduct.objects.create(order=order, product=product, quantity=quantity)

        # Recalculer le montant total
        order.calculate_total()
        order.save()

        return UpdateOrder(order=order)

# Mutation pour créer une commande
class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        products = graphene.List(ProductInput, required=True)
        status = StatusEnum(required=False, default_value="UNCONFIRMED")
        payment_method = PaymentMethodEnum(required=True)
        delivery_address_id = graphene.ID(required=True)
        billing_address_id = graphene.ID(required=False)

    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, products, status, payment_method, delivery_address_id, billing_address_id=None):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise GraphQLError("Client non trouvé.")

        try:
            delivery_address = Address.objects.get(pk=delivery_address_id)
        except Address.DoesNotExist:
            raise GraphQLError("Adresse de livraison non trouvée.")

        billing_address = None
        if billing_address_id:
            try:
                billing_address = Address.objects.get(pk=billing_address_id)
            except Address.DoesNotExist:
                raise GraphQLError("Adresse de facturation non trouvée.")

        if not products:
            raise GraphQLError("La liste des produits est vide.")

        order = Order(
            customer=customer,
            total_amount=0,
            status=status.value,
            payment_method=payment_method.value,
            delivery_address=delivery_address,
            billing_address=billing_address
        )
        order.save()

        for item in products:
            try:
                product = Product.objects.get(pk=item.product_id)
            except Product.DoesNotExist:
                raise GraphQLError(f"Produit avec l'ID {item.product_id} non trouvé.")

            quantity = item.quantity
            if quantity <= 0:
                raise GraphQLError("La quantité doit être supérieure à zéro.")

            OrderProduct.objects.create(order=order, product=product, quantity=quantity)

        # Calculer le montant total après ajout des produits
        order.calculate_total()
      

        return CreateOrder(order=order)

# Mutation pour supprimer une commande
class DeleteOrder(graphene.Mutation):
    class Arguments:
        order_id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, order_id):
        try:
            order = Order.objects.get(pk=order_id)
            order.delete()
            return DeleteOrder(success=True)
        except Order.DoesNotExist:
            raise GraphQLError("Commande non trouvée.")

# Mutation pour modifier le statut d'une commande
class UpdateOrderStatus(graphene.Mutation):
    class Arguments:
        order_id = graphene.ID(required=True)
        status = StatusEnum(required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, order_id, status):
        try:
            order = Order.objects.get(pk=order_id)
            order.status = status.value
            order.save()
            return UpdateOrderStatus(order=order)
        except Order.DoesNotExist:
            raise GraphQLError("Commande non trouvée.")




# Définition des Mutations
class Mutation(graphene.ObjectType):
    create_order = CreateOrder.Field()
    delete_order = DeleteOrder.Field()
    update_order_status = UpdateOrderStatus.Field()
    update_order = UpdateOrder.Field()
   



# Schéma GraphQL final
schema = graphene.Schema(query=Query, mutation=Mutation)
