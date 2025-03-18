import graphene
from graphene_django.types import DjangoObjectType
from .models import Address

# Enumération des pays basée sur le modèle Django
class CountryEnum(graphene.Enum):
    TUNISIE = "Tunisie"
    FRANCE = "France"
    ALLEMAGNE = "Allemagne"
    ITALIE = "Italie"
    ESPAGNE = "Espagne"
    ETATS_UNIS = "États-Unis"
    CANADA = "Canada"
    ROYAUME_UNI = "Royaume-Uni"

# Définition du type GraphQL pour Address
class AddressType(DjangoObjectType):
    class Meta:
        model = Address
        fields = ('id', 'street', 'city', 'postal_code', 'country')

# Mutation pour créer une adresse
class CreateAddress(graphene.Mutation):
    class Arguments:
        street = graphene.String(required=True)
        city = graphene.String(required=True)
        postal_code = graphene.String(required=True)
        country = CountryEnum(required=True)  # Utilisation de l'enum

    address = graphene.Field(AddressType)

    def mutate(self, info, street, city, postal_code, country):
        address = Address(
            street=street,
            city=city,
            postal_code=postal_code,
            country=country.value # Conversion de l'énumération en string
        )
        address.save()
        return CreateAddress(address=address)

# Mutation pour mettre à jour une adresse
class UpdateAddress(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        street = graphene.String()
        city = graphene.String()
        postal_code = graphene.String()
        country = CountryEnum()  # Utilisation de l'enum

    address = graphene.Field(AddressType)

    def mutate(self, info, id, street=None, city=None, postal_code=None, country=None):
        address = Address.objects.get(pk=id)
        if street:
            address.street = street
        if city:
            address.city = city
        if postal_code:
            address.postal_code = postal_code
        if country:
            address.country=country.value  # Conversion de l'énumération en string
        address.save()
        return UpdateAddress(address=address)

# Mutation pour supprimer une adresse
class DeleteAddress(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        address = Address.objects.get(pk=id)
        address.delete()
        return DeleteAddress(success=True)

# Définir les requêtes
class Query(graphene.ObjectType):
    all_addresses = graphene.List(AddressType)
    address = graphene.Field(AddressType, id=graphene.ID(required=True))

    def resolve_all_addresses(self, info):
        return Address.objects.all()

    def resolve_address(self, info, id):
        return Address.objects.get(pk=id)

# Définir les mutations
class Mutation(graphene.ObjectType):
    create_address = CreateAddress.Field()
    update_address = UpdateAddress.Field()
    delete_address = DeleteAddress.Field()

# Schéma principal
schema = graphene.Schema(query=Query, mutation=Mutation)
