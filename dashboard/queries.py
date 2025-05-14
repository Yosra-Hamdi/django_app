from django.db.models import Sum, Count, F
from orders.models import Order
from products.models import Product
from customers.models import Customer
from django.utils import timezone
from datetime import timedelta

def get_dashboard_stats():
    """Récupère toutes les statistiques pour le tableau de bord"""
    
    # Statistiques de base
    stats = {
        'total_orders': Order.objects.count(),
        'total_customers': Customer.objects.count(),
        'total_products': Product.objects.count(),
    }
   
    
    # Statistiques sur 7 jours
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    orders_last_7_days = Order.objects.filter(
        creation_date__gte=seven_days_ago
    )
    
    stats.update({
        'recent_orders_count': orders_last_7_days.count(),
        'recent_revenue': orders_last_7_days.aggregate(
            total=Sum('total_amount')
        )['total'] or 0,
        'recent_customers': Customer.objects.filter(
            date_joined__gte=seven_days_ago
        ).count(),
    })
     # Top 5 des produits les plus vendus (quantité + CA)
    stats['top_selling_products'] = Product.objects.annotate(
        units_sold=Count('orderproduct'),
        revenue=Sum(F('orderproduct__quantity') * F('orderproduct__unit_price_ht'))
    ).order_by('-units_sold')[:5]
    
    # Commandes récentes
    stats['recent_orders'] = Order.objects.order_by('-creation_date')[:5]
    
    
    return stats