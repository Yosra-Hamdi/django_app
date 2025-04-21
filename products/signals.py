from datetime import datetime , date
from decimal import Decimal
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from stock_mvt.models import StockMovement
from .models import Product, ProductHistory
import json

User = get_user_model()

def get_current_user():
    """Récupère l'utilisateur actuel de manière synchrone ou asynchrone"""
    from django.utils.functional import SimpleLazyObject
    from django.contrib.auth.middleware import get_user

    def get_user_from_request():
        import inspect
        for frame_record in inspect.stack():
            frame = frame_record[0]
            request = frame.f_locals.get('request')
            if request and hasattr(request, 'user'):
                return request.user
        return None

    user = get_user_from_request()
    if user is None:
        return SimpleLazyObject(lambda: None)
    return user


@receiver(pre_save, sender=Product)
def product_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Product.objects.get(pk=instance.pk)
            instance._old_instance = old_instance
        except Product.DoesNotExist:
            pass
@receiver(post_save, sender=Product)
def product_post_save(sender, instance, created, **kwargs):
    user = None
    
    # 1. Essayer de récupérer depuis le contexte de requête
    try:
        from django.utils.functional import SimpleLazyObject
        from django.contrib.auth.middleware import get_user
        request = getattr(instance, '_request', None)
        if request:
            user = request.user if hasattr(request, 'user') else None
    except:
        pass
    
    # 2. Fallback pour l'application (GraphQL)
    if (not user or user.is_anonymous) and hasattr(instance, '_request_user'):
        user = instance._request_user
    
    # 3. Fallback pour les scripts/commandes
    if not user or user.is_anonymous:
        try:
            user = User.objects.get(username='system')  # Créez un utilisateur système
        except User.DoesNotExist:
            pass
    
    if created:
        action = 'CREATE'
        ProductHistory.objects.create(
            product=instance,
            user=user if user and not user.is_anonymous else None,
            action=action,
            new_value=serialize_product(instance)
        )
    else:
        old_instance = getattr(instance, '_old_instance', None)
        if old_instance:
            changed_fields = {}
            old_values = {}
            new_values = {}
            
            for field in instance._meta.fields:
                field_name = field.name
                old_val = getattr(old_instance, field_name)
                new_val = getattr(instance, field_name)
                
                if old_val != new_val:
                    changed_fields[field_name] = {
                        'old': serialize_value(old_val),
                        'new': serialize_value(new_val)
                    }
                    old_values[field_name] = serialize_value(old_val)
                    new_values[field_name] = serialize_value(new_val)
            
            if changed_fields:
                action = 'UPDATE'
                ProductHistory.objects.create(
                    product=instance,
                    user=user if user and not user.is_anonymous else None,
                    action=action,
                    old_value=old_values,
                    new_value=new_values,
                    changed_fields=changed_fields
                )
def serialize_value(value):
    """Sérialise une valeur pour le stockage JSON"""
    if value is None:
        return None
    elif isinstance(value, (str, int, float, bool)):
        return value
    elif isinstance(value, Decimal):
        return str(value)
    elif isinstance(value, (datetime, date)):
        return value.isoformat()
    elif hasattr(value, '__str__'):
        return str(value)
    else:
        return repr(value)




def serialize_product(product):
    from django.forms.models import model_to_dict
    
    data = model_to_dict(product, exclude=['image'])
    
    # Gestion spéciale pour les relations et types complexes
    if hasattr(product, 'category') and product.category:
        data['category'] = str(product.category)
    
    # Conversion des types non sérialisables
    for field, value in data.items():
        if isinstance(value, Decimal):
            data[field] = str(value)
        elif isinstance(value, (datetime, date)):
            data[field] = value.isoformat()
        elif hasattr(value, '__str__'):
            data[field] = str(value)
    
    return data

@receiver(post_save, sender=StockMovement)
def ensure_user_on_stock_movement(sender, instance, created, **kwargs):
    if not instance.user_id:
        # Réessaye de définir l'utilisateur si absent
        if hasattr(instance, '_current_user'):
            instance.user = instance._current_user
            instance.save(update_fields=['user'])