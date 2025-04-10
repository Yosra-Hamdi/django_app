
from decimal import Decimal
import graphene
from graphene_django import DjangoObjectType
from categories.schema import CategoryType
from products.models import Category, Product
from django.core.files.uploadedfile import InMemoryUploadedFile
from graphene_file_upload.scalars import Upload



class ProductType(DjangoObjectType):
    vat_amount = graphene.Float()
    price_excluding_vat = graphene.Float()
    price_including_vat = graphene.Float()
    category_name = graphene.String()

    class Meta:
        model = Product
        fields = "__all__"
    
    def resolve_vat_amount(self, info):
        return self.vat_amount

    def resolve_price_excluding_vat(self, info):
        return self.price_excluding_vat

    def resolve_price_including_vat(self, info):
        return self.price_including_vat

    def resolve_category_name(self, info):
        return self.category.name if self.category else None

    def resolve_image(self, info):
        if self.image:
            return info.context.build_absolute_uri(self.image.url)
        return None






class Query(graphene.ObjectType):
    all_products = graphene.List(ProductType)
    product_by_id = graphene.Field(ProductType, id=graphene.Int())
    products_by_category = graphene.List(ProductType, category_id=graphene.Int())
    all_categories = graphene.List(CategoryType)
    search_products = graphene.List(ProductType, name=graphene.String(required=True))
    
    def resolve_all_products(root, info):
        return Product.objects.select_related('category').all()
    
    def resolve_product_by_id(root, info, id):
        try:
            return Product.objects.select_related('category').get(id=id)
        except Product.DoesNotExist:
            return None
    
    def resolve_products_by_category(root, info, category_id):
        return Product.objects.filter(category_id=category_id)
    
    def resolve_all_categories(root, info):
        return Category.objects.all()
    
    def resolve_search_products(self, info, name):
        return Product.objects.filter(name__icontains=name)
   
  # Mutations pour Product  
class CreateProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    initial_stock = graphene.Int(  # Nouveau champ pour la quantité initiale
        default_value=0,
        description="Quantité initiale en stock"
    )
    category_id = graphene.Int()
    unit = graphene.String(default_value="kg")
    purchase_price = graphene.Decimal()
    selling_price = graphene.Decimal(required=True)
    vat_rate = graphene.Decimal(default_value=0.000)
    include_vat = graphene.Boolean(default_value=False)
    image = Upload()

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = CreateProductInput(required=True)

    product = graphene.Field(ProductType)

    @classmethod
    def mutate(cls, root, info, input):
        try:
            # Convertir les Decimal en float si nécessaire
            input_data = dict(input)
            initial_stock = input_data.pop('initial_stock', 0)  
            for field in ['purchase_price', 'selling_price', 'vat_rate']:
                if field in input_data and input_data[field] is not None:
                    input_data[field] = Decimal(input_data[field])
            
            # Gestion séparée de l'image
            image = input_data.pop('image', None)
            product = Product(**input_data)
            
            if image and isinstance(image, InMemoryUploadedFile):
                product.image = image
            
            product.save()
            # Création ou mise à jour du stock associé
            if hasattr(product, 'stock'):
                product.stock.quantity = initial_stock
                product.stock.save()
            else:
                from stock.models import Stock  # Import local pour éviter les circular imports
                Stock.objects.create(product=product, quantity=initial_stock)
            

            return CreateProduct(product=product)
        except Exception as e:
            raise Exception(f"Erreur lors de la création du produit: {str(e)}")

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
 
    create_product = CreateProduct.Field()
    update_product = UpdateProduct.Field()
    delete_product = DeleteProduct.Field()
    delete_all_products = DeleteAllProducts.Field()
 # Ajouter la nouvelle mutation
schema = graphene.Schema(query=Query, mutation=Mutation)