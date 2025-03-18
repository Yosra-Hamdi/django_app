
import graphene
from graphene_django import DjangoObjectType
from products.models import Category, Product


class CategoryType(DjangoObjectType):



    class Meta:
        model = Category
        fields = ("id", "name")

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock_quantity", "category", "unit", "image")
    
    def resolve_image(self, info):
        if self.image:
            return self.image.url  # Retourne l'URL complète de l'image
        return None

# Mutations pour Category
class CreateCategory(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)

    category = graphene.Field(CategoryType)

    def mutate(self, info, name):
        category = Category(name=name)
        category.save()
        return CreateCategory(category=category)

class UpdateCategory(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        name = graphene.String(required=True)

    category = graphene.Field(CategoryType)

    def mutate(self, info, id, name):
        category = Category.objects.get(id=id)
        category.name = name
        category.save()
        return UpdateCategory(category=category)

class DeleteCategory(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        category = Category.objects.get(id=id)
        category.delete()
        return DeleteCategory(success=True)

# Mutations pour Product
class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Decimal(required=True)
        stock_quantity = graphene.Int(required=True)
        category_id = graphene.Int()
        unit = graphene.String()
        image = graphene.String()

    product = graphene.Field(ProductType)

    def mutate(self, info, name, price, stock_quantity, category_id, unit, image=None):
        category = Category.objects.get(id=category_id) if category_id else None
        product = Product(name=name, price=price, stock_quantity=stock_quantity, category=category, unit=unit, image=image)
        product.save()
        return CreateProduct(product=product)

class UpdateProduct(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        name = graphene.String(required=True)
        price = graphene.Decimal(required=True)
        stock_quantity = graphene.Int(required=True)
        category_id = graphene.Int()
        unit = graphene.String()
        image = graphene.String()

    product = graphene.Field(ProductType)

    def mutate(self, info, id, name, price, stock_quantity, category_id, unit, image=None):
        product = Product.objects.get(id=id)
        category = Category.objects.get(id=category_id) if category_id else None
        product.name = name
        product.price = price
        product.stock_quantity = stock_quantity
        product.category = category
        product.unit = unit
        if image is not None:
            product.image = image
        product.save()
        return UpdateProduct(product=product)

class DeleteProduct(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        product = Product.objects.get(id=id)
        if product.image:
            product.image.delete(save=False)
        product.delete()
        return DeleteProduct(success=True)

# Nouvelle mutation pour mettre à jour le stock
class UpdateProductStock(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)  # ID du produit
        quantity = graphene.Int(required=True)  # Quantité à soustraire du stock

    product = graphene.Field(ProductType)  # Retourne le produit mis à jour

    def mutate(self, info, id, quantity):
        # Récupérer le produit par son ID
        product = Product.objects.get(id=id)

        # Vérifier si la quantité en stock est suffisante
        if product.stock_quantity < quantity:
            raise Exception("Stock insuffisant")

        # Mettre à jour le stock
        product.stock_quantity -= quantity
        product.save()

        # Retourner le produit mis à jour
        return UpdateProductStock(product=product)

# Classe Mutation principale pour inclure toutes les mutations
class Mutation(graphene.ObjectType):
    create_category = CreateCategory.Field()
    update_category = UpdateCategory.Field()
    delete_category = DeleteCategory.Field()

    create_product = CreateProduct.Field()
    update_product = UpdateProduct.Field()
    delete_product = DeleteProduct.Field()

    update_product_stock = UpdateProductStock.Field()  # Ajouter la nouvelle mutation

class Query(graphene.ObjectType):
    products = graphene.List(ProductType)
    categories = graphene.List(CategoryType)

    def resolve_products(root, info):
        return Product.objects.all()
    
    def resolve_categories(root, info):
        return Category.objects.all()

schema = graphene.Schema(query=Query, mutation=Mutation)