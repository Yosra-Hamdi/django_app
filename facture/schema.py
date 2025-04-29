


from datetime import datetime, timedelta
from graphene_django import DjangoObjectType
import graphene
from django.utils import timezone 
from graphql import GraphQLError

from deliveryNote.models import DeliveryNote
from facture.models import Invoice
from orders.models import Order

class InvoiceType(DjangoObjectType):
    class Meta:
        model = Invoice
        fields = "__all__"

class InvoiceQuery(graphene.ObjectType):
    invoice_by_order = graphene.Field(InvoiceType, order_id=graphene.ID(required=True))

    def resolve_invoice_by_order(self, info, order_id):
        try:
            return Invoice.objects.get(order_id=order_id)
        except Invoice.DoesNotExist:
            return None

class CreateOrGetInvoice(graphene.Mutation):
    class Arguments:
        order_id = graphene.ID(required=True)
        due_date = graphene.String(required=False)
       

    invoice = graphene.Field(InvoiceType)
    created = graphene.Boolean()

    def mutate(self, info, order_id, **kwargs):
        try:
            # Vérifier si une facture existe déjà
            invoice = Invoice.objects.filter(order_id=order_id).first()
            created = False
            
            if not invoice:
                # Créer une nouvelle facture si elle n'existe pas
                order = Order.objects.get(pk=order_id)
                due_date = kwargs.get('due_date')
                
                if not due_date:
                    due_date = (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                
                invoice = Invoice.objects.create(
                    order=order,
                    due_date=due_date,
                    
                )
                created = True
            
            return CreateOrGetInvoice(invoice=invoice, created=created)
            
        except Order.DoesNotExist:
            raise GraphQLError("Commande non trouvée")
        except Exception as e:
            raise GraphQLError(f"Erreur: {str(e)}")

class Mutation(graphene.ObjectType):
    create_or_get_invoice = CreateOrGetInvoice.Field()