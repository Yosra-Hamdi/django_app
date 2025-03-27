from graphene_django import DjangoObjectType
import graphene
from graphene import Enum
from addresses.schema import AddressType
from authentification.models import User
from customers.models import Customer
from products.models import Product
from addresses.models import Address
from .models import Notification, Order, OrderProduct
from graphql import GraphQLError
from .beams_config import beams_client



# Enum pour les statuts de la commande
class StatusEnum(Enum):
    UNCONFIRMED = "UNCONFIRMED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    PAID = "PAID"
    DELIVERED = "DELIVERED"

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

    class Meta:
        model = Order
        fields = ("id", "products", "customer", "total_amount", "status", "creation_date", "payment_method", "delivery_address", "billing_address")

    # Calcul du montant total
    def resolve_total_amount(self, info):
        return self.calculate_total()

# Type GraphQL pour Notification
class NotificationType(DjangoObjectType):
    order_id = graphene.Int()  

    class Meta:
        model = Notification
        fields = ("id", "title", "body", "is_read", "created_at" )

    def resolve_order_id(self, info):
        return self.order.id if self.order else None  
    
    

# Requêtes GraphQL
class Query(graphene.ObjectType):
    orders = graphene.List(OrderType)
    order = graphene.Field(OrderType, id=graphene.ID(required=True))
    notifications = graphene.List(NotificationType)

    def resolve_orders(root, info):
        return Order.objects.all()

    def resolve_order(root, info, id):
        try:
            return Order.objects.get(pk=id)
        except Order.DoesNotExist:
            raise GraphQLError("Commande non trouvée.")
        
    def resolve_notifications(root, info):
        user = info.context.user 
        if not user.is_authenticated:
            raise GraphQLError("Authentification requise.")
        return Notification.objects.filter(user=user).order_by('-created_at')    
  

   
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
        admin_user = User.objects.get(username="admin")
         # Enregistrer la notification pour l'admin
        Notification.objects.create(
            user=admin_user,
            title="Nouvelle commande reçue",
            body=f"Une nouvelle commande a été passée : Commande #{order.id}",
            order=order
        )

        # Envoyer la notification via Pusher Beams
        beams_client.publish_to_users(
            user_ids=[str(admin_user.id)],  # ID de l'utilisateur qui gère les commandes
            publish_body={
                'fcm': {
                    'notification': {
                        'title': 'Nouvelle commande',
                        'body': f"Une nouvelle commande a été reçue : Commande #{order.id}",
                    },
                },
            },
        )

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



# Mutation pour marquer une notification comme lue
class MarkNotificationAsRead(graphene.Mutation):
    class Arguments:
        notification_id = graphene.ID(required=True)
    success = graphene.Boolean()

    def mutate(self, info, notification_id):
        try:
            notification = Notification.objects.get(pk=notification_id)
            notification.is_read = True
            notification.save()
            return MarkNotificationAsRead(success=True)
        except Notification.DoesNotExist:
            return MarkNotificationAsRead(success=False)



# Définition des Mutations
class Mutation(graphene.ObjectType):
    create_order = CreateOrder.Field()
    delete_order = DeleteOrder.Field()
    update_order_status = UpdateOrderStatus.Field()
    update_order = UpdateOrder.Field()
    mark_notification_as_read = MarkNotificationAsRead.Field()



# Schéma GraphQL final
schema = graphene.Schema(query=Query, mutation=Mutation)
