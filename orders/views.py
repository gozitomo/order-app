from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Order

# Create your views here.

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})
