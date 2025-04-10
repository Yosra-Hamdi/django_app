from graphene_django.types import DjangoObjectType
import graphene
from categories.models import Category
from graphene import Mutation, ObjectType, String, Int, Boolean


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = ('id', 'name') 
        


class CreateCategory(Mutation):
    class Arguments:
        name = String(required=True)  # Champs nécessaires pour créer une catégorie

    category = graphene.Field(CategoryType)

    def mutate(self, info, name):
        category = Category(name=name)
        category.save()
        return CreateCategory(category=category)

class UpdateCategory(Mutation):
    class Arguments:
        id = Int(required=True)  # ID de la catégorie à mettre à jour
        name = String(required=True)  # Nouveau nom de la catégorie

    category = graphene.Field(CategoryType)

    def mutate(self, info, id, name):
        try:
            category = Category.objects.get(id=id)
            category.name = name
            category.save()
            return UpdateCategory(category=category)
        except Category.DoesNotExist:
            raise Exception("Category not found")

class DeleteCategory(Mutation):
    class Arguments:
        id = Int(required=True)  # ID de la catégorie à supprimer

    success = Boolean()

    def mutate(self, info, id):
        try:
            category = Category.objects.get(id=id)
            category.delete()
            return DeleteCategory(success=True)
        except Category.DoesNotExist:
            raise Exception("Category not found")


class DeleteAllCategories(Mutation):
    success = Boolean()

    def mutate(self, info):
        Category.objects.all().delete()
        return DeleteAllCategories(success=True)

class Query(ObjectType):
    categories = graphene.List(CategoryType)
    search_category = graphene.List(
        CategoryType,
        name=String(required=True)
    )
    def resolve_categories(self, info):
        return Category.objects.all()
    def resolve_search_category(self, info, name):
        return Category.objects.filter(name__icontains=name)

class Mutation(ObjectType):
    create_category = CreateCategory.Field()
    update_category = UpdateCategory.Field()
    delete_category = DeleteCategory.Field()
    delete_all_categories = DeleteAllCategories.Field() 



schema = graphene.Schema(query=Query, mutation=Mutation)