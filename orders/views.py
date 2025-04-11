from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.timezone import localdate
from .models import Order, OrderItem
from products.models import Product
from .utils import calculate_sipping_fee
from .forms import CustomSignupForm

# Create your views here.

def signup(request):
    if request.method == 'POST':
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            address = form.cleand_data['address']
            UserProfile.objects.create(user=user, address=address)
            login(request, user)
            return redirect('order_history')
    else:
        form = CustomSignupForm()
    return render(request, 'orders/signup.html', {'form': form})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    today = localdate()
    for order in orders:
        #print(order.created_at.date(), localdate())
        #本日注文分以外をキャンセル不可とする
        if order.created_at.date() != today:
            order.status = 'キャンセル不可'
            order.save()
    return render(request, 'orders/order_history.html', {'orders': orders})

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {
        'order': order,
        })

def place_order(request):
    products = Product.objects.all()

    if request.method == 'POST':
        #新しい注文を作成
        order = Order.objects.create(user=request.user)

        total_quantity = 0
        total_price = 0
        tax =0
        total_tax =0

        for product in products:
            qty = request.POST.get(f'quantity_{product.id}')
            if qty and int(qty) > 0:
                quantity = int(qty)
                total_quantity += quantity
                subtotal = product.price * quantity
                total_price += subtotal
                tax = subtotal / 1.08 * 0.08
                total_tax += tax

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=int(qty),
                    subtotal=subtotal,
                    tax = tax
                )

        order.total_quantity = total_quantity
        order.total = total_price
        order.shipping_fee = calculate_sipping_fee(total_quantity)
        order.shipping_tax = order.shipping_fee /1.1 * 0.1
        order.final_total = order.total + order.shipping_fee
        order.final_tax = total_tax + order.shipping_tax
        order.save()

        return redirect('order_detail', order_id = order.id)
        #リダイレクト先は注文確認画面
        #return redirect('order_history')

    return render(request, 'orders/place_order.html', {'products': products})

@login_required
@require_POST
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'キャンセル':
        messages.info(request, "すでにキャンセル済みです。")
    elif order.status == 'キャンセル不可':
        messages.error(request, "この注文は当日以外キャンセルできません。/n Lineまたはお電話にてお問い合わせくださいませ。")
    else:
        order.status = 'キャンセル'
        order.save()
        messages.success(request, "注文をキャンセルしました。")

    #リダイレクト先は注文詳細
    return redirect('order_detail', order_id=order.id)
