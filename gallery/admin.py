
from django.contrib import admin

from gallery.models import GalleryImage , ProductImage
# Register your models here.
admin.site.register(GalleryImage)
admin.site.register( ProductImage)
