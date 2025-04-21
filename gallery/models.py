from django.db import models
from products.models import Product



class GalleryImage(models.Model):
    """Stocke toutes les images uploadées dans l'application"""
    image = models.ImageField(upload_to='gallery/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image {self.id}"
 

    

class ProductImage(models.Model):
    """Relie les produits aux images de la galerie"""
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='product_images') 
    gallery_image = models.ForeignKey(GalleryImage, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)



    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'une seule image principale
        if self.is_primary:
            ProductImage.objects.filter(product=self.product).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image {self.id} pour {self.product.name}"
