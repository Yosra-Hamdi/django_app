from datetime import datetime, timedelta
from graphene_django import DjangoObjectType
import graphene
from django.utils import timezone
from graphql import GraphQLError
from graphene import InputObjectType

from facture.models import Invoice, InvoiceItem
from orders.models import Order
from customers.models import Customer
from products.models import Product
from addresses.models import Address

class InvoiceItemType(DjangoObjectType):
    class Meta:
        model = InvoiceItem
        fields = "__all__"

class InvoiceType(DjangoObjectType):
    company_info = graphene.JSONString()
    items = graphene.List(InvoiceItemType)

    class Meta:
        model = Invoice
        fields = "__all__"

    def resolve_company_info(self, info):
        return self.company_info
    
    def resolve_items(self, info):
        return self.items.all()

class InvoiceItemInput(InputObjectType):
    product_id = graphene.ID(required=False)
    quantity = graphene.Decimal(required=True)
    unit_price_ht = graphene.Decimal(required=False)
    vat_rate = graphene.Decimal(required=False)

class InvoiceInput(InputObjectType):
    order_id = graphene.ID(required=False)
    customer_id = graphene.ID(required=False)
    billing_address_id = graphene.ID(required=False)
    delivery_address_id = graphene.ID(required=False)
    due_date = graphene.String(required=True)
    payment_method = graphene.String(required=False)
    delivery_method = graphene.String(required=False)
    notes = graphene.String(required=False)
    items = graphene.List(InvoiceItemInput, required=False)

class InvoiceQuery(graphene.ObjectType):
    invoice_by_order = graphene.Field(InvoiceType, order_id=graphene.ID(required=True))
    invoice_by_id = graphene.Field(InvoiceType, invoice_id=graphene.ID(required=True))
    all_invoices = graphene.List(InvoiceType)

    def resolve_invoice_by_order(self, info, order_id):
        try:
            return Invoice.objects.get(order_id=order_id)
        except Invoice.DoesNotExist:
            return None

    def resolve_invoice_by_id(self, info, invoice_id):
        try:
            return Invoice.objects.get(id=invoice_id)
        except Invoice.DoesNotExist:
            return None

    def resolve_all_invoices(self, info):
        return Invoice.objects.all().order_by('-issue_date')

class CreateInvoiceFromOrder(graphene.Mutation):
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
                    customer=order.customer,
                    billing_address=order.billing_address,
                    delivery_address=order.delivery_address,
                    payment_method=order.payment_method,
                    delivery_method=order.delivery_method,
                    due_date=due_date,
                )
                
                # Copier les produits de la commande vers la facture
                for order_product in order.products.all():
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        product=order_product.product,
                        quantity=order_product.quantity,
                        unit_price_ht=order_product.unit_price_ht,
                        vat_rate=order_product.vat_rate,
                    )
                
                invoice.calculate_totals()
                created = True
            
            return CreateInvoiceFromOrder(invoice=invoice, created=created)
            
        except Order.DoesNotExist:
            raise GraphQLError("Commande non trouvée")
        except Exception as e:
            raise GraphQLError(f"Erreur: {str(e)}")

class CreateManualInvoice(graphene.Mutation):
    class Arguments:
        invoice_data = InvoiceInput(required=True)

    invoice = graphene.Field(InvoiceType)

    def mutate(self, info, invoice_data):
        try:
            # Validation des données
            if not invoice_data.get('customer_id'):
                raise GraphQLError("Un client doit être spécifié")
            
            if not invoice_data.get('billing_address_id'):
                raise GraphQLError("Une adresse de facturation doit être spécifiée")
            
            if not invoice_data.get('items') or len(invoice_data['items']) == 0:
                raise GraphQLError("Au moins un produit doit être ajouté")
            
            # Création de la facture
            invoice = Invoice.objects.create(
                customer_id=invoice_data['customer_id'],
                billing_address_id=invoice_data['billing_address_id'],
                delivery_address_id=invoice_data.get('delivery_address_id'),
                due_date=invoice_data['due_date'],
                payment_method=invoice_data.get('payment_method', 'CASH'),
                delivery_method=invoice_data.get('delivery_method', 'DELIVERY'),
                notes=invoice_data.get('notes'),
            )
            
            # Ajout des produits
            for item_data in invoice_data['items']:
                # Si c'est un produit existant, utilisez son prix
                if item_data.get('product_id'):
                    product = Product.objects.get(id=item_data['product_id'])
                    unit_price_ht = product.price_excluding_vat
                    vat_rate = product.vat_rate
                else:
                    unit_price_ht = item_data.get('unit_price_ht', 0)
                    vat_rate = item_data.get('vat_rate', 0)

                InvoiceItem.objects.create(
                    invoice=invoice,
                    product_id=item_data.get('product_id'),
                    quantity=item_data['quantity'],
                    unit_price_ht=unit_price_ht,
                    vat_rate=vat_rate,
                )
            
            invoice.calculate_totals()
            
            return CreateManualInvoice(invoice=invoice)
            
        except Exception as e:
            raise GraphQLError(f"Erreur lors de la création de la facture: {str(e)}")



class DeleteInvoice(graphene.Mutation):
    class Arguments:
        invoice_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, invoice_id):
        try:
            # Trouver la facture
            invoice = Invoice.objects.get(id=invoice_id)
            
            # Supprimer la facture (les InvoiceItem associés seront supprimés automatiquement
            # grâce à on_delete=CASCADE dans le modèle)
            invoice.delete()
            
            return DeleteInvoice(success=True, message="Facture supprimée avec succès")
            
        except Invoice.DoesNotExist:
            return DeleteInvoice(success=False, message="Facture non trouvée")
        except Exception as e:
            return DeleteInvoice(success=False, message=f"Erreur: {str(e)}")


class Mutation(graphene.ObjectType):
    create_invoice_from_order = CreateInvoiceFromOrder.Field()
    create_manual_invoice = CreateManualInvoice.Field()
    delete_invoice = DeleteInvoice.Field()  # Ajouter cette ligne

schema = graphene.Schema(query=InvoiceQuery, mutation=Mutation)