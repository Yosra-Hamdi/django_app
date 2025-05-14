import graphene
from graphene_django.types import DjangoObjectType
from django.db.models import Sum, Count
from datetime import timedelta
from django.utils import timezone
from orders.models import Order
from products.models import Product
from customers.models import Customer
from django.db.models import Count, Sum, F

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = '__all__'

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = '__all__'

class DailySalesType(graphene.ObjectType):
    date = graphene.String()
    amount = graphene.Float()


class ProductSalesType(graphene.ObjectType):
    product = graphene.Field(ProductType)  # Utilise votre ProductType existant
    units_sold = graphene.Int()
    revenue = graphene.Float()



class DashboardStatsType(graphene.ObjectType):
    # Statistiques de base
    total_orders = graphene.Int()
    total_customers = graphene.Int()
    total_products = graphene.Int()
    top_selling_products = graphene.List(ProductSalesType)
    
    # Statistiques récentes (7 jours)
    recent_orders_count = graphene.Int()
    recent_revenue = graphene.Float()
    recent_customers = graphene.Int()
    
    # Données détaillées
    recent_orders = graphene.List(OrderType)
    popular_products = graphene.List(ProductType)
    
    # Données pour graphiques
    sales_over_time = graphene.List(DailySalesType)  # 30 derniers jours
    weekly_comparison = graphene.List(graphene.Float)  # Comparaison semaine actuelle vs précédente

class Query(graphene.ObjectType):
    dashboard_stats = graphene.Field(DashboardStatsType)
    
    def resolve_dashboard_stats(self, info):
        # Calcul des dates importantes
        today = timezone.now().date()
        seven_days_ago = today - timedelta(days=7)
        thirty_days_ago = today - timedelta(days=30)
        
        # 1. Statistiques de base
        stats = {
            'total_orders': Order.objects.count(),
            'total_customers': Customer.objects.count(),
            'total_products': Product.objects.count(),
        }
        
        # 2. Statistiques récentes (7 jours)
        recent_orders = Order.objects.filter(creation_date__gte=seven_days_ago)
        stats.update({
            'recent_orders_count': recent_orders.count(),
            'recent_revenue': recent_orders.aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
            'recent_customers': Customer.objects.filter(
                date_joined__gte=seven_days_ago
            ).count(),
        })

     
        
        # 3. Données détaillées
        stats.update({
            'recent_orders': Order.objects.order_by('-creation_date')[:5],
            'popular_products': Product.objects.annotate(
                order_count=Count('orderproduct')
            ).order_by('-order_count')[:5],
        })
        
        # 4. Données pour graphiques
        # a. Données sur 30 jours
        sales_data = []
        for i in range(30, -1, -1):
            date = today - timedelta(days=i)
            daily_sales = Order.objects.filter(
                creation_date__date=date
            ).aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            
            sales_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'amount': float(daily_sales)
            })
        
        # b. Comparaison hebdomadaire
        current_week = [
            float(Order.objects.filter(
                creation_date__date=today - timedelta(days=i)
            ).aggregate(total=Sum('total_amount'))['total'] or 0)
            for i in range(7)
        ]
        
        previous_week = [
            float(Order.objects.filter(
                creation_date__date=today - timedelta(days=i+7)
            ).aggregate(total=Sum('total_amount'))['total'] or 0)
            for i in range(7)
        ]
        
        stats.update({
            'sales_over_time': sales_data,
            'weekly_comparison': [
                sum(current_week),
                sum(previous_week)
            ],
        })
        top_products = Product.objects.annotate(
            units_sold=Count('orderproduct'),
            revenue=Sum(F('orderproduct__quantity') * F('orderproduct__unit_price_ht'))
        ).order_by('-units_sold')[:5]

        stats['top_selling_products'] = [
            {
                'product': product,
                'units_sold': product.units_sold,
                'revenue': float(product.revenue or 0)
            }
            for product in top_products
        ]

        
        
        return stats