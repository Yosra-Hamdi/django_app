from graphene_django import DjangoObjectType
import graphene
from graphene import Decimal
from addresses.schema import AddressType
from authentification.models import User
from customers.models import Customer
from products.models import Product
from addresses.models import Address
from .models import Order, OrderProduct
from graphql import GraphQLError
from django.utils import timezone

# Enum pour les statuts de la commande
class StatusEnum(graphene.Enum):
    UNCONFIRMED = "UNCONFIRMED"
    CONFIRMED = "CONFIRMED"
    STOCK_VERIFICATION = "STOCK_VERIFICATION"
    PREPARATION = "PREPARATION"
    PACKAGING = "PACKAGING"
    WAITING_FOR_PAYMENT = "WAITING_FOR_PAYMENT"
    PAYMENT_ERROR = "PAYMENT_ERROR"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    DELIVERED_PAID = "DELIVERED_PAID"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"

# Enum pour les méthodes de paiement
class PaymentMethodEnum(graphene.Enum):
    CASH = "CASH"
    CARD = "CARD"

# Type GraphQL pour OrderProduct
class OrderProductType(DjangoObjectType):
    total_ht = graphene.Float()
    vat_amount = graphene.Float()
    total_ttc = graphene.Float()

    class Meta:
        model = OrderProduct
        fields = "__all__"

    def resolve_total_ht(self, info):
        return float(self.total_ht)

    def resolve_vat_amount(self, info):
        return float(self.vat_amount)

    def resolve_total_ttc(self, info):
        return float(self.total_ttc)

# Type GraphQL pour Order
class OrderType(DjangoObjectType):
    subtotal_ht = graphene.Float()
    total_vat = graphene.Float()
    total_ttc = graphene.Float()
    order_number = graphene.String()

    class Meta:
        model = Order
        fields = "__all__"

    def resolve_subtotal_ht(self, info):
        return float(self.subtotal_ht)

    def resolve_total_vat(self, info):
        return float(self.total_vat)

    def resolve_total_ttc(self, info):
        return float(self.total_ttc)

    def resolve_order_number(self, info):
        return self.generate_order_number()

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

# Mutation pour créer une commande
class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        products = graphene.List(ProductInput, required=True)
        status = StatusEnum(required=False)
        payment_method = PaymentMethodEnum(required=True)
        delivery_address_id = graphene.ID(required=True)
        billing_address_id = graphene.ID(required=False)
        user_id = graphene.ID(required=False)

    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, products, payment_method, delivery_address_id, status=None, billing_address_id=None, user_id=None):
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

        user = None
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                pass

        if not products:
            raise GraphQLError("La liste des produits est vide.")

        order = Order(
            customer=customer,
            status=status.value if status else 'UNCONFIRMED',
            payment_method=payment_method.value,
            delivery_address=delivery_address,
            billing_address=billing_address,
            user=user
        )
        order.save()

        for item in products:
            try:
                product = Product.objects.get(pk=item.product_id)
            except Product.DoesNotExist:
                raise GraphQLError(f"Produit avec l'ID {item.product_id} non trouvé.")

            if item.quantity <= 0:
                raise GraphQLError("La quantité doit être supérieure à zéro.")

            OrderProduct.objects.create(
                order=order,
                product=product,
                quantity=item.quantity
            )

        order.calculate_totals()
        return CreateOrder(order=order)

# Mutation pour mettre à jour une commande
class UpdateOrder(graphene.Mutation):
    class Arguments:
        order_id = graphene.ID(required=True)
        products = graphene.List(ProductInput, required=False)
        status = StatusEnum(required=False)
        payment_method = PaymentMethodEnum(required=False)
        delivery_address_id = graphene.ID(required=False)
        billing_address_id = graphene.ID(required=False)
        user_id = graphene.ID(required=False)

    order = graphene.Field(OrderType)

    def mutate(self, info, order_id, products=None, status=None, payment_method=None, 
               delivery_address_id=None, billing_address_id=None, user_id=None):
        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            raise GraphQLError("Commande non trouvée.")

        if status:
            old_status = order.status
            order.status = status.value
            order.update_stock_on_status_change(old_status, status.value)

        if payment_method:
            order.payment_method = payment_method.value

        if delivery_address_id:
            try:
                order.delivery_address = Address.objects.get(pk=delivery_address_id)
            except Address.DoesNotExist:
                raise GraphQLError("Adresse de livraison non trouvée.")

        if billing_address_id:
            try:
                order.billing_address = Address.objects.get(pk=billing_address_id)
            except Address.DoesNotExist:
                raise GraphQLError("Adresse de facturation non trouvée.")

        if user_id:
            try:
                order.user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                pass

        if products is not None:
            order.products.all().delete()
            for item in products:
                try:
                    product = Product.objects.get(pk=item.product_id)
                except Product.DoesNotExist:
                    raise GraphQLError(f"Produit avec l'ID {item.product_id} non trouvé.")

                if item.quantity <= 0:
                    raise GraphQLError("La quantité doit être supérieure à zéro.")

                OrderProduct.objects.create(
                    order=order,
                    product=product,
                    quantity=item.quantity
                )

        order.save()
        order.calculate_totals()
        return UpdateOrder(order=order)

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
            old_status = order.status
            order.status = status.value
            order.save()
            order.update_stock_on_status_change(old_status, status.value)
            return UpdateOrderStatus(order=order)
        except Order.DoesNotExist:
            raise GraphQLError("Commande non trouvée.")

# Définition des Mutations
class Mutation(graphene.ObjectType):
    create_order = CreateOrder.Field()
    update_order = UpdateOrder.Field()
    delete_order = DeleteOrder.Field()
    update_order_status = UpdateOrderStatus.Field()

# Schéma GraphQL final
schema = graphene.Schema(query=Query, mutation=Mutation)