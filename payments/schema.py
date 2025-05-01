import graphene
from graphene_django import DjangoObjectType
from .models import Payment
from .constants import PAYMENT_METHOD_CHOICES, PAYMENT_STATUS_CHOICES
from orders.models import Order
from graphql import GraphQLError
from django.utils import timezone

class PaymentType(DjangoObjectType):
    class Meta:
        model = Payment
        fields = "__all__"
        
    payment_method_display = graphene.String()
    status_display = graphene.String()
    
    def resolve_payment_method_display(self, info):
        return self.get_payment_method_display()
    
    def resolve_status_display(self, info):
        return self.get_status_display()

class PaymentMethodEnum(graphene.Enum):
    CASH = 'CASH'
    CARD = 'CARD'

class PaymentStatusEnum(graphene.Enum):
    PENDING = 'PENDING'
    PAID = 'PAID'
    FAILED = 'FAILED'

class PaymentInput(graphene.InputObjectType):
    order_id = graphene.ID(required=True)
    amount = graphene.Float(required=True)
    payment_method = PaymentMethodEnum(required=True)
    transaction_id = graphene.String()

class UpdatePaymentStatusInput(graphene.InputObjectType):
    payment_id = graphene.ID(required=True)
    status = PaymentStatusEnum(required=True)
    transaction_id = graphene.String()

class CreatePayment(graphene.Mutation):
    class Arguments:
        input = PaymentInput(required=True)

    payment = graphene.Field(PaymentType)

    def mutate(self, info, input):
        try:
            order = Order.objects.get(pk=input.order_id)
        except Order.DoesNotExist:
            raise GraphQLError("Commande introuvable")

        payment = Payment(
            order=order,
            amount=input.amount,
            payment_method=input.payment_method,
            transaction_id=input.transaction_id,
            status='PENDING'  # Toujours PENDING au départ, même pour CASH
        )
        
        payment.save()
        return CreatePayment(payment=payment)

class UpdatePaymentStatus(graphene.Mutation):
    class Arguments:
        input = UpdatePaymentStatusInput(required=True)

    payment = graphene.Field(PaymentType)

    def mutate(self, info, input):
        try:
            payment = Payment.objects.get(pk=input.payment_id)
        except Payment.DoesNotExist:
            raise GraphQLError("Paiement introuvable")

        payment.status = input.status
        if input.transaction_id:
            payment.transaction_id = input.transaction_id
        
        payment.save()
        return UpdatePaymentStatus(payment=payment)

class PaymentQuery(graphene.ObjectType):
    payments = graphene.List(PaymentType)
    payment = graphene.Field(PaymentType, id=graphene.ID(required=True))
    payments_by_order = graphene.List(PaymentType, order_id=graphene.ID(required=True))

    def resolve_payments(self, info):
        return Payment.objects.all()

    def resolve_payment(self, info, id):
        try:
            return Payment.objects.get(pk=id)
        except Payment.DoesNotExist:
            raise GraphQLError("Paiement introuvable")

    def resolve_payments_by_order(self, info, order_id):
        try:
            order = Order.objects.get(pk=order_id)
            return order.payments.all()
        except Order.DoesNotExist:
            raise GraphQLError("Commande introuvable")

class PaymentMutation(graphene.ObjectType):
    create_payment = CreatePayment.Field()
    update_payment_status = UpdatePaymentStatus.Field()