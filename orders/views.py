from django.shortcuts import render
from .models import Order
from notification.models import Notification

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST





def dashboard_view(request):
    return render(request, 'orders/dashboard.html', {
        'PUSHER_BEAMS_INSTANCE_ID': '578cdb56-625d-4b55-810a-71fb27bbef7b'  # À passer au template
    })
def order_details_view(request):
    return render(request, 'orders/order_details.html', {
        'PUSHER_BEAMS_INSTANCE_ID': '578cdb56-625d-4b55-810a-71fb27bbef7b'  # À passer au template
    })
def notification_count(request):
    count = Notification.objects.filter(user=request.user, read=False).count()
    return JsonResponse({'count': count})