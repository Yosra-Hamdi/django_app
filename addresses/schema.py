import graphene
from graphene_django.types import DjangoObjectType
from .models import Address

# Enumération des gouvernorats
class GovernorateEnum(graphene.Enum):
    TUNIS = "Tunis"
    ARIANA = "Ariana"
    BEN_AROUS = "Ben Arous"
    MANOUBA = "Manouba"
    NABEUL = "Nabeul"
    ZAGHOUAN = "Zaghouan"
    BIZERTE = "Bizerte"
    BEJA = "Béja"
    JENDOUBA = "Jendouba"
    KEF = "Kef"
    SILIANA = "Siliana"
    SOUSSE = "Sousse"
    MONASTIR = "Monastir"
    MAHDIA = "Mahdia"
    KAIROUAN = "Kairouan"
    KASSERINE = "Kasserine"
    SIDI_BOUZID = "Sidi Bouzid"
    SFAX = "Sfax"
    GABES = "Gabès"
    MEDENINE = "Medenine"
    TATAOUINE = "Tataouine"
    GAFSA = "Gafsa"
    TOZEUR = "Tozeur"
    KEBILI = "Kebili"

# Définition du type GraphQL
class AddressType(DjangoObjectType):
    class Meta:
        model = Address
        fields = ('id', 'street', 'city', 'postal_code', 'governorate')

# Mutation pour créer une adresse
class CreateAddress(graphene.Mutation):
    class Arguments:
        street = graphene.String(required=True)
        city = graphene.String(required=True)
        postal_code = graphene.String(required=True)
        governorate = GovernorateEnum(required=True)

    address = graphene.Field(AddressType)

    def mutate(self, info, street, city, postal_code, governorate):
        address = Address(
            street=street,
            city=city,
            postal_code=postal_code,
            governorate=governorate.value
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
        governorate = GovernorateEnum()

    address = graphene.Field(AddressType)

    def mutate(self, info, id, street=None, city=None, postal_code=None, governorate=None):
        address = Address.objects.get(pk=id)
        if street:
            address.street = street
        if city:
            address.city = city
        if postal_code:
            address.postal_code = postal_code
        if governorate:
            address.governorate = governorate.value
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

# Requêtes
class Query(graphene.ObjectType):
    all_addresses = graphene.List(AddressType)
    address = graphene.Field(AddressType, id=graphene.ID(required=True))

    def resolve_all_addresses(self, info):
        return Address.objects.all()

    def resolve_address(self, info, id):
        return Address.objects.get(pk=id)

# Mutations
class Mutation(graphene.ObjectType):
    create_address = CreateAddress.Field()
    update_address = UpdateAddress.Field()
    delete_address = DeleteAddress.Field()

# Schéma
schema = graphene.Schema(query=Query, mutation=Mutation)
