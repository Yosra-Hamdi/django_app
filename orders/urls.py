from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.order_dashboard, name='order_dashboard'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('notifications/<int:notification_id>/mark-read/',
          views.mark_notification_as_read, 
          name='mark_notification_read'),



]