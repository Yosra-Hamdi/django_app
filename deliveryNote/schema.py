
from datetime import datetime
from graphene_django import DjangoObjectType
import graphene
from django.utils import timezone 
from graphql import GraphQLError

from deliveryNote.models import DeliveryNote
from orders.models import Order

class DeliveryNoteType(DjangoObjectType):
    customer_info = graphene.JSONString()
    products_info = graphene.JSONString()
    payment_info = graphene.JSONString()
    company_info = graphene.JSONString()

    class Meta:
        model = DeliveryNote
        fields = '__all__'

    def resolve_customer_info(self, info):
        return self.customer_info

    def resolve_products_info(self, info):
        return self.products_info

    def resolve_payment_info(self, info):
        return self.payment_info
    def resolve_company_info(self, info):  # 🔥 AJOUT ICI
        return self.company_info


class DeliveryNoteQuery(graphene.ObjectType):
    delivery_note = graphene.Field(DeliveryNoteType, id=graphene.ID(required=True))
    delivery_notes = graphene.List(
        DeliveryNoteType,
        order_id=graphene.ID(),
        date_from=graphene.String(),
        date_to=graphene.String(),
        is_delivered=graphene.Boolean()
    )

    def resolve_delivery_note(self, info, id):
        try:
            return DeliveryNote.objects.get(pk=id)
        except DeliveryNote.DoesNotExist:
            raise GraphQLError("Bon de livraison non trouvé")

    def resolve_delivery_notes(self, info, order_id=None, date_from=None, date_to=None, is_delivered=None):
        queryset = DeliveryNote.objects.all()
        
        if order_id:
            queryset = queryset.filter(order__id=order_id)
        
        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            queryset = queryset.filter(delivery_date__gte=date_from)
        
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            queryset = queryset.filter(delivery_date__lte=date_to)
        
        if is_delivered is not None:
            queryset = queryset.filter(is_delivered=is_delivered)
        
        return queryset.order_by('-delivery_date')

class Query(graphene.ObjectType):
   
    
    delivery_note = graphene.Field(DeliveryNoteType, id=graphene.ID(required=True))
    delivery_notes = graphene.List(
        DeliveryNoteType,
        order_id=graphene.ID(),
        date_from=graphene.String(),
        date_to=graphene.String(),
        is_delivered=graphene.Boolean()
    )

    def resolve_delivery_note(self, info, id):
        return DeliveryNoteQuery().resolve_delivery_note(info, id)

    def resolve_delivery_notes(self, info, **kwargs):
        return DeliveryNoteQuery().resolve_delivery_notes(info, **kwargs)



class CreateDeliveryNote(graphene.Mutation):
    class Arguments:
        order_id = graphene.ID(required=True)
        delivery_date = graphene.String(required=False)

    delivery_note = graphene.Field(DeliveryNoteType)

    def mutate(self, info, order_id, delivery_date=None):
        try:
            order = Order.objects.get(pk=order_id)
            
            if delivery_date:
                try:
                    delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d').date()
                except ValueError:
                    raise GraphQLError("Format de date invalide. Utilisez YYYY-MM-DD")
            else:
                delivery_date = timezone.now().date()

            # Créez d'abord sans référence
            delivery_note = DeliveryNote(
                order=order,
                delivery_date=delivery_date
            )
            # La méthode save() générera automatiquement la référence
            delivery_note.save()

            return CreateDeliveryNote(delivery_note=delivery_note)
        except Order.DoesNotExist:
            raise GraphQLError("Commande non trouvée")
        except Exception as e:
            raise GraphQLError(f"Erreur lors de la création: {str(e)}")

class MarkAsDelivered(graphene.Mutation):
    class Arguments:
        delivery_note_id = graphene.ID(required=True)

    delivery_note = graphene.Field(DeliveryNoteType)

    def mutate(self, info, delivery_note_id):
        try:
            delivery_note = DeliveryNote.objects.get(pk=delivery_note_id)
            delivery_note.mark_as_delivered()
            return MarkAsDelivered(delivery_note=delivery_note)
        except DeliveryNote.DoesNotExist:
            raise GraphQLError("Bon de livraison non trouvé")

class Mutation(graphene.ObjectType):
    create_delivery_note = CreateDeliveryNote.Field()
    mark_as_delivered = MarkAsDelivered.Field()