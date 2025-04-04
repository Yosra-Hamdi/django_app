
import graphene
from graphene_django import DjangoObjectType
from products.models import Category, Product
from django.core.files.uploadedfile import InMemoryUploadedFile
from graphene_file_upload.scalars import Upload

class CategoryType(DjangoObjectType):



    class Meta:
        model = Category
        fields = ("id", "name")

class ProductType(DjangoObjectType):
    vat_amount = graphene.Float()
    price_excluding_vat = graphene.Float()
    price_including_vat = graphene.Float()

    class Meta:
        model = Product
        fields = ("id", "name", "stock_quantity", "category", "unit", "image", "purchase_price", "selling_price", 
            "vat_rate", "include_vat")
    
    def resolve_vat_amount(self, info):
        return float(self.vat_amount)

    def resolve_price_excluding_vat(self, info):
        return float(self.price_excluding_vat)

    def resolve_price_including_vat(self, info):
        return float(self.price_including_vat)




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





class Query(graphene.ObjectType):
    all_products = graphene.List(ProductType)
    product_by_id = graphene.Field(ProductType, id=graphene.Int())
    products_by_category = graphene.List(ProductType, category_id=graphene.Int())
    categories = graphene.List(CategoryType)
    search_products = graphene.List(ProductType, name=graphene.String(required=True))
    
    def resolve_all_products(root, info):
        return Product.objects.all()
    
    def resolve_product_by_id(root, info, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            return None
    def resolve_products_by_category(root, info, category_id):
        return Product.objects.filter(category_id=category_id)
    def resolve_search_products(self, info, name):
        return Product.objects.filter(name__icontains=name)
    
  # Mutations pour Product  
class CreateProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    stock_quantity = graphene.Int(required=True)
    category_id = graphene.Int()
    unit = graphene.String()
    purchase_price = graphene.Float()
    selling_price = graphene.Float(required=True)
    vat_rate = graphene.Float()
    include_vat = graphene.Boolean()
    image = Upload()

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = CreateProductInput(required=True)

    product = graphene.Field(ProductType)

    @classmethod
    def mutate(cls, root, info, input):
        # Gestion de l'image séparément
        image = input.pop('image', None)
        
        product = Product(**input)
        
        if image and isinstance(image, InMemoryUploadedFile):
            product.image = image
        
        product.save()
        return CreateProduct(product=product)
    
    #
class UpdateProductInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    name = graphene.String()
    stock_quantity = graphene.Int()
    category_id = graphene.Int()
    unit = graphene.String()
    purchase_price = graphene.Float()
    selling_price = graphene.Float()
    vat_rate = graphene.Float()
    include_vat = graphene.Boolean()
    image = Upload()
class UpdateProduct(graphene.Mutation):
    class Arguments:
        input = UpdateProductInput(required=True)

    product = graphene.Field(ProductType)

    @classmethod
    def mutate(cls, root, info, input):
        product_id = input.pop('id')
        image = input.pop('image', None)
        
        try:
            product = Product.objects.get(id=product_id)
            for field, value in input.items():
                if value is not None:
                    setattr(product, field, value)
            
            if image and isinstance(image, InMemoryUploadedFile):
                product.image = image
            
            product.save()
            return UpdateProduct(product=product)
        except Product.DoesNotExist:
            return None

class DeleteProduct(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, id):
        try:
            product = Product.objects.get(id=id)
            product.delete()
            return DeleteProduct(success=True, message="Produit supprimé avec succès")
        except Product.DoesNotExist:
            return DeleteProduct(success=False, message="Produit non trouvé")

class DeleteAllProducts(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()
    deleted_count = graphene.Int()

    @classmethod
    def mutate(cls, root, info):
        try:
            # Compte le nombre de produits avant suppression
            count = Product.objects.count()
            
            # Supprime tous les produits
            deleted_count, _ = Product.objects.all().delete()
            
            return DeleteAllProducts(
                success=True,
                message=f"{deleted_count} produits supprimés avec succès",
                deleted_count=deleted_count
            )
        except Exception as e:
            return DeleteAllProducts(
                success=False,
                message=f"Erreur lors de la suppression: {str(e)}",
                deleted_count=0
            )
# Classe Mutation principale pour inclure toutes les mutations
class Mutation(graphene.ObjectType):
    create_category = CreateCategory.Field()
    update_category = UpdateCategory.Field()
    delete_category = DeleteCategory.Field()
    create_product = CreateProduct.Field()
    update_product = UpdateProduct.Field()
    Delete_product = DeleteProduct.Field()
    delete_all_products = DeleteAllProducts.Field()
 # Ajouter la nouvelle mutation
schema = graphene.Schema(query=Query, mutation=Mutation)