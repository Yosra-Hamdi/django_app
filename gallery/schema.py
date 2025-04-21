import graphene
from graphene_django import DjangoObjectType
from django.core.files.base import ContentFile
import base64



from .models import GalleryImage, Product, ProductImage

class GalleryImageType(DjangoObjectType):
    class Meta:
        model = GalleryImage
        fields = "__all__"


class ProductImageType(DjangoObjectType):
    class Meta:
        model = ProductImage
        fields =  "__all__"

        
class UploadImage(graphene.Mutation):
    class Arguments:
        file = graphene.String(required=True)  # Image en base64
    
    image = graphene.Field(GalleryImageType)
    
    @classmethod
    def mutate(cls, root, info, file):
        # Décoder l'image base64
        format, imgstr = file.split(';base64,') 
        ext = format.split('/')[-1]
        image_data = ContentFile(base64.b64decode(imgstr), name=f'upload.{ext}')
        
        gallery_image = GalleryImage(image=image_data)
        gallery_image.save()
        return UploadImage(image=gallery_image)


class Query(graphene.ObjectType):
    all_images = graphene.List(GalleryImageType)
    image = graphene.Field(GalleryImageType, id=graphene.ID(required=True))

    def resolve_all_images(root, info):
        return GalleryImage.objects.all()

    def resolve_image(root, info, id):
        try:
            return GalleryImage.objects.get(id=id)
        except GalleryImage.DoesNotExist:
            return None

class SetPrimaryImage(graphene.Mutation):
    class Arguments:
        product_id = graphene.ID(required=True)
        image_id = graphene.ID(required=True)

    success = graphene.Boolean()
    

    @classmethod
    def mutate(cls, root, info, product_id, image_id):
        try:
            product_image = ProductImage.objects.get(
                product_id=product_id,
                gallery_image_id=image_id
            )
            
            # Marquer cette image comme principale
            product_image.is_primary = True
            product_image.save()
            
            return SetPrimaryImage(success=True)
        except ProductImage.DoesNotExist:
            raise Exception("Cette image n'est pas associée au produit")

class Mutation(graphene.ObjectType):
    upload_image = UploadImage.Field()
    set_primary_image = SetPrimaryImage.Field()


gallery_schema = graphene.Schema(query=Query, mutation=Mutation)