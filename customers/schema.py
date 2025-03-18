import graphene
from graphene_django import DjangoObjectType
from customers.models import Customer

# Definition of the GraphQL type for Client
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "last_name", "first_name", "email", "phone", "address")

# Definition of queries
class Query(graphene.ObjectType):
    all_customer = graphene.List(CustomerType)
    customer = graphene.Field(CustomerType, id=graphene.ID(required=True))

    def resolve_all_customer(root, info):
        return Customer.objects.all()

    def resolve_customer(root, info, id):
        try:
            return Customer.objects.get(pk=id)
        except Customer.DoesNotExist:
            return None

# Final schema
schema = graphene.Schema(query=Query)
