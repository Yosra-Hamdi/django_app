from django.shortcuts import render
from .models import Order
from notification.models import Notification

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST




