import graphene
from graphene_django import DjangoObjectType
from addresses.models import Address
from customers.models import Customer
from django.db.models import Q

from orders.schema import OrderType

# Definition of the GraphQL type for Client
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"
        
    orders = graphene.List(lambda: OrderType)
    order_count = graphene.Int()
    total_spent = graphene.Float()

    def resolve_orders(self, info):
        return self.orders.all()


    def resolve_order_count(self, info):
        return self.orders.count()

    def resolve_total_spent(self, info):
        return sum(order.total_amount for order in self.orders.all())
# Input type for search
class CustomerSearchInput(graphene.InputObjectType):
    search_term = graphene.String(required=True)

# Definition of queries
class Query(graphene.ObjectType):
    all_customer = graphene.List(CustomerType)
    customer = graphene.Field(CustomerType, id=graphene.ID(required=True))
    search_customers = graphene.List(
        CustomerType,
        search_input=CustomerSearchInput(required=True)
    )
 
    def resolve_all_customer(root, info):
        return Customer.objects.all()

    def resolve_customer(root, info, id):
        try:
            return Customer.objects.get(pk=id)
        except Customer.DoesNotExist:
            return None

    def resolve_search_customers(root, info, search_input):
        search_term = search_input.search_term
        return Customer.objects.filter(
            Q(last_name__icontains=search_term) |
            Q(first_name__icontains=search_term) |
            Q(email__icontains=search_term) |
            Q(phone__icontains=search_term)
        )

# Input types for mutations
class CustomerInput(graphene.InputObjectType):
    id = graphene.ID()
    last_name = graphene.String(required=True)
    first_name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=True)
    address_id = graphene.ID()

# Mutations
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)

    @staticmethod
    def mutate(root, info, input):
        address = None
        if input.address_id:
            address = Address.objects.get(pk=input.address_id)
        
        customer = Customer(
            last_name=input.last_name,
            first_name=input.first_name,
            email=input.email,
            phone=input.phone,
            address=address
        )
        customer.save()
        return CreateCustomer(customer=customer)
class UpdateCustomer(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)

    @staticmethod
    def mutate(root, info, id, input):
        try:
            customer = Customer.objects.get(pk=id)
            address = None
            if input.address_id:
                address = Address.objects.get(pk=input.address_id)
            
            customer.last_name = input.last_name
            customer.first_name = input.first_name
            customer.email = input.email
            customer.phone = input.phone
            customer.address = address
            customer.save()
            return UpdateCustomer(customer=customer)
        except Customer.DoesNotExist:
            return None
class DeleteCustomer(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, info, id):
        try:
            customer = Customer.objects.get(pk=id)
            customer.delete()
            return DeleteCustomer(success=True)
        except Customer.DoesNotExist:
            return DeleteCustomer(success=False)
        

# Add mutations to root Mutation class
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    update_customer = UpdateCustomer.Field()
    delete_customer = DeleteCustomer.Field()

# Final schema
schema = graphene.Schema(query=Query, mutation=Mutation)
