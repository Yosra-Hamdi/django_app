from django.shortcuts import render
from .models import Order, Notification
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST




def order_dashboard(request):
    orders = Order.objects.all().order_by('-creation_date')
    notifications = Notification.objects.all().order_by('-created_at')
    return render(request, 'orders/dashboard.html', {
        'orders': orders,
        'notifications': notifications,
    })

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/order_detail.html', {'order': order})



@require_POST

def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_read = True
    notification.save()
    return JsonResponse({
        'success': True,
        'order_id': notification.order.id if notification.order else None
    })