
import graphene
from graphene_django.types import DjangoObjectType

from addresses.models import Address
from .models import CompanyInfo

# Définition du type CompanyInfo
class CompanyInfoType(DjangoObjectType):
    class Meta:
        model = CompanyInfo
        fields = "__all__"

# Définition de la mutation pour créer une CompanyInfo
class CreateCompanyInfo(graphene.Mutation):
    company_info = graphene.Field(CompanyInfoType)

    class Arguments:
        name = graphene.String(required=True)
        address = graphene.Int(required=True)  # Utilisez 'address' au lieu de 'address_id'
        phone = graphene.String()
        email = graphene.String()
        logo = graphene.String()

    def mutate(self, info, name, address, phone=None, email=None, logo=None):
        try:
            address_obj = Address.objects.get(id=address)
            company_info = CompanyInfo.objects.create(
                name=name,
                address=address_obj,  # Passez l'objet Address
                phone=phone,
                email=email,
                logo=logo
            )
            return CreateCompanyInfo(company_info=company_info)
        except Address.DoesNotExist:
            raise Exception("Address with this ID does not exist")

# Définition de la Query (existant déjà)
class Query(graphene.ObjectType):
    company_info = graphene.Field(CompanyInfoType)

    def resolve_company_info(self, info):
        return CompanyInfo.objects.first()

# Ajout de la mutation au schéma
class Mutation(graphene.ObjectType):
    create_company_info = CreateCompanyInfo.Field()

# Mise à jour du schéma pour inclure la mutation
schema = graphene.Schema(query=Query, mutation=Mutation)
