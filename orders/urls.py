from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('order_details/', views.order_details_view , name='order_details'),
]



