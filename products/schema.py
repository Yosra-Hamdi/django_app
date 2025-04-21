
from decimal import Decimal
import graphene
from graphene_django import DjangoObjectType
from categories.schema import CategoryType
from gallery.models import GalleryImage, ProductImage
from gallery.schema import GalleryImageType, ProductImageType
from products.models import Category, Product, ProductHistory
from django.core.files.uploadedfile import InMemoryUploadedFile
from graphene_file_upload.scalars import Upload

from stock.models import Stock






class ProductHistoryType(DjangoObjectType):
    action_display = graphene.String()
    user_email = graphene.String()
    user_name = graphene.String()
    class Meta:
        model = ProductHistory
        fields = '__all__'

    def resolve_action_display(self, info):
        return self.get_action_display()
    
    def resolve_user_email(self, info):
        return self.user.email if self.user else None
    
    def resolve_user_name(self, info):
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}".strip()
        return None

class ProductType(DjangoObjectType):
    vat_amount = graphene.Float()
    price_excluding_vat = graphene.Float()
    price_including_vat = graphene.Float()
    category_name = graphene.String()
    product_images = graphene.List(ProductImageType)
    updated_at = graphene.DateTime()
    history = graphene.List(ProductHistoryType)



    class Meta:
        model = Product
        fields = "__all__"

    def resolve_history(self, info):
        return self.history.all().order_by('-timestamp')
    
    def resolve_vat_amount(self, info):
        return self.vat_amount

    def resolve_price_excluding_vat(self, info):
        return self.price_excluding_vat

    def resolve_price_including_vat(self, info):
        return self.price_including_vat

    def resolve_category_name(self, info):
        return self.category.name if self.category else None

    def resolve_product_images(self, info):
        return self.product_images.all()
    def resolve_updated_at(self, info):
        return self.updated_at


class Query(graphene.ObjectType):
    all_products = graphene.List(ProductType)
    product_by_id = graphene.Field(ProductType, id=graphene.Int())
    products_by_category = graphene.List(ProductType, category_id=graphene.Int())
    search_products = graphene.List(ProductType, name=graphene.String(required=True))
    product_history = graphene.List(
        ProductHistoryType,
        product_id=graphene.ID(required=True),
        limit=graphene.Int(),
        offset=graphene.Int()
    )





    def resolve_all_products(root, info):
        return Product.objects.select_related('category').all()
    
    def resolve_product_by_id(root, info, id):
        try:
            return Product.objects.select_related('category').get(id=id)
        except Product.DoesNotExist:
            return None
    
    def resolve_products_by_category(root, info, category_id):
        return Product.objects.filter(category_id=category_id)
    
   
    def resolve_search_products(self, info, name):
        return Product.objects.filter(name__icontains=name)
    
    def resolve_product_history(self, info, product_id, limit=None, offset=None):

        queryset = ProductHistory.objects.filter(product_id=product_id).order_by('-timestamp')
        
        if offset:
            queryset = queryset[offset:]
        if limit:
            queryset = queryset[:limit]
            
        return queryset
  # Mutations pour Product  
class CreateProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    initial_stock = graphene.Int(  default_value=0, description="Quantité initiale en stock")
    category_id = graphene.Int()
    unit = graphene.String(default_value="kg")
    purchase_price = graphene.Decimal()
    selling_price = graphene.Decimal(required=True)
    vat_rate = graphene.Decimal(default_value=0.000)
    include_vat = graphene.Boolean(default_value=False)
    gallery_image_ids = graphene.List(graphene.ID) 
    primary_image_id = graphene.ID() # ID de l'image principale

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = CreateProductInput(required=True)

    product = graphene.Field(ProductType)

    @classmethod
    def mutate(cls, root, info, input):
        try:
            user = info.context.user
            if not user or user.is_anonymous:
                raise Exception("Authentification requise")

            # Convertir l'input
            input_data = dict(input)
            
            # Créer le produit avec l'utilisateur explicitement
            product = Product(
                **{k: v for k, v in input_data.items() if k not in ['initial_stock', 'gallery_image_ids', 'primary_image_id']}
            )
            
            # Stocker l'utilisateur de manière explicite
            product._current_user = user
            product.save()


            # Conversion des Decimal
            input_data = dict(input)
            initial_stock = input_data.pop('initial_stock', 0)
            gallery_image_ids = input_data.pop('gallery_image_ids', [])
            primary_image_id = input_data.pop('primary_image_id', None)
            
            for field in ['purchase_price', 'selling_price', 'vat_rate']:
                if field in input_data and input_data[field] is not None:
                    input_data[field] = Decimal(input_data[field])
            
            # Création du produit
            product = Product(**input_data)
            product._request_user = info.context.user  # Ajoutez cette ligne
            product.save()
            
              # Lier les images de la galerie
            primary_image_id = input_data.pop('primary_image_id', None)
            for image_id in gallery_image_ids:
                gallery_image = GalleryImage.objects.get(id=image_id)
                product_image = ProductImage.objects.create(
                    product=product,
                    gallery_image=gallery_image,
                    is_primary=(str(image_id) == str(primary_image_id))
            )
            
            # Gestion du stock
            if hasattr(product, 'stock'):
                product.stock.quantity = initial_stock
                product.stock.save()
            else:
                Stock.objects.create(product=product, quantity=initial_stock)
            return CreateProduct(product=product)
            
        except Exception as e:
            raise Exception(f"Erreur lors de la création du produit: {str(e)}")

class UpdateProductInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    name = graphene.String()
    initial_stock = graphene.Int(description="Quantité initiale en stock")
    category_id = graphene.Int()
    unit = graphene.String()
    purchase_price = graphene.Decimal()
    selling_price = graphene.Decimal()
    vat_rate = graphene.Decimal()
    include_vat = graphene.Boolean()
    gallery_image_ids = graphene.List(graphene.ID)
    primary_image_id = graphene.ID()  # ID de l'image principale


class UpdateProduct(graphene.Mutation):
    class Arguments:
        input = UpdateProductInput(required=True)

    product = graphene.Field(ProductType)

    @classmethod
    def mutate(cls, root, info, input):
        try:
            user = info.context.user
            input_data = dict(input)
            product_id = input_data.pop('id')
            initial_stock = input_data.pop('initial_stock', None)
            gallery_image_ids = input_data.pop('gallery_image_ids', [])
            primary_image_id = input_data.pop('primary_image_id', None)

            # Récupérer le produit
            product = Product.objects.get(id=product_id)
            product._request_user = info.context.user  # Ajoutez cette ligne

            # Mettre à jour les champs de base
            for field, value in input_data.items():
                if value is not None:
                    setattr(product, field, value)

            product.save()

            # Gestion du stock
            if initial_stock is not None and hasattr(product, 'stock'):
                product.stock.quantity = initial_stock
                product.stock.save()

            # Gestion des images
            if gallery_image_ids:
                # Supprimer les anciennes associations d'images
                ProductImage.objects.filter(product=product).delete()
                
                # Créer les nouvelles associations
                for image_id in gallery_image_ids:
                    gallery_image = GalleryImage.objects.get(id=image_id)
                    ProductImage.objects.create(
                        product=product,
                        gallery_image=gallery_image,
                        is_primary=(str(image_id) == str(primary_image_id))
                    )
            
            # Si seulement primary_image_id est fourni (sans gallery_image_ids)
            elif primary_image_id:
                try:
                    # Marquer l'image existante comme principale
                    product_image = ProductImage.objects.get(
                        product=product,
                        gallery_image_id=primary_image_id
                    )
                    ProductImage.objects.filter(product=product).update(is_primary=False)
                    product_image.is_primary = True
                    product_image.save()
                except ProductImage.DoesNotExist:
                    pass

            return UpdateProduct(product=product)
            
        except Product.DoesNotExist:
            raise Exception("Produit non trouvé")
        except GalleryImage.DoesNotExist:
            raise Exception("Une ou plusieurs images de galerie n'existent pas")
        except Exception as e:
            raise Exception(f"Erreur lors de la mise à jour du produit: {str(e)}")

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