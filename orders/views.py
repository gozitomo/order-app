from datetime import date, timedelta
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.views.decorators.http import require_POST
from django.utils.timezone import localdate, now
from .models import Order, OrderItem, Invoice
from products.models import Product
from users.models import User
from .utils import calculate_sipping_fee
from .forms import CustomSignupForm
from weasyprint import HTML

# Create decorators

def admin_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)

def top_page(request):
    return render(request, 'orders/top.html')

# Create your views here.

def signup(request):
    if request.method == 'POST':
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            address = form.cleaned_data['address']
            UserProfile.objects.create(user=user, address=address)
            login(request, user)
            return redirect('order_history')
    else:
        form = CustomSignupForm()
    return render(request, 'orders/signup.html', {'form': form})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
    today = localdate()
    for order in orders:
        #print(order.created_at.date(), localdate())
        #本日注文分以外をキャンセル不可とする
        if order.created_at.date() != today:
            order.status = 'キャンセル不可'
            order.save()
    return render(request, 'orders/order_history.html', {'orders': orders, today: today})

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
        tax = 0
        total_tax = 0
        total_shipping_fee = 0

        for product in products:
            qty = request.POST.get(f'quantity_{product.id}')
            if qty and int(qty) > 0:
                quantity = int(qty)
                total_quantity += quantity
                subtotal = product.price * quantity
                total_price += subtotal
                shipping_fee = calculate_sipping_fee(quantity)
                shipping_tax = shipping_fee / 1.1 * 0.1
                total_shipping_fee += shipping_fee
                total_shipping_tax = total_shipping_fee / 1.1 * 0.1
                tax = subtotal / 1.08 * 0.08
                total_tax += tax

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=int(qty),
                    subtotal=subtotal,
                    shipping_fee = shipping_fee,
                    tax = tax,
                    shipping_tax = shipping_tax,
                )

        order.total_quantity = total_quantity
        order.total_price = total_price
        order.total_shipping_fee = total_shipping_fee
        order.shipping_tax = total_shipping_tax
        order.final_total = order.total_price + order.total_shipping_fee
        order.total_tax = total_tax
        order.save()

        return redirect('order_detail', order_id = order.id)
        #リダイレクト先は注文確認画面
        #return redirect('order_history')

    return render(request, 'orders/place_order.html', {'products': products})

def order_invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    html_string = render_to_string('orders/invoice_pdf.html', {'order': order})
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="invoice_{order.id}.pdf"'
    return response



def invoice_pdf(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    #アクセス制限：ログインユーザー自身orスタッフならOK
    if request.user != invoice.user and not request.user.is_staff:
        return HttpResponseForbidden("アクセス権限がありません。")

    items = invoice.items.all().select_related('product', 'order')

    html = render_to_string('orders/invoice_pdf.html', {
        'invoice': invoice,
        'items': items,
        'user': invoice.user,
    })

    pdf_file = HTML(string=html).write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="invoice_{invoice.invoice_id}.pdf"'
    return response

def my_invoices(request):
    invoices = Invoice.objects.filter(user=request.user).order_by('-issued_date')
    return render(request, 'orders/my_invoice_list.html', {'invoices': invoices})

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

@admin_required
def monthly_invoice_pdf(request):
    today = date.today()
    today = today - timedelta(days=60)
    first_day_this_month = today.replace(day=1)
    last_day_last_month = first_day_this_month - timedelta(days=1)
    first_day_last_month = last_day_last_month.replace(day=1)
    users = User.objects.all()

    for user in users:

        items = OrderItem.objects.filter(
            order__user=user,
            invoice_id__isnull=True,
            delivery_date__gte=first_day_last_month,
            delivery_date__lte=last_day_last_month,
            order__status__in=['未処理', '完了', 'キャンセル不可'] #キャンセル除外
        )

        if not items.exists():
            continue

        invoice = Invoice.objects.create(
            user = user,
            invoice_type = 'monthly',
            invoice_id = Invoice.generate_invoice_number(),
            issued_date = today,
            period_start = first_day_last_month,
            period_end = last_day_last_month,
            total_price = sum(item.subtotal for item in items),
            tax8 = sum(item.tax for item in items),
            shipping_fee = sum(item.shipping_fee for item in items),
            tax10 = sum(item.shipping_tax for item in items),
            total_extax = 0,
            shipping_extax = 0,
            final_price = 0,
            final_tax = 0,
            final_extax = 0,
        )
        invoice.total_extax = invoice.total_price - invoice.tax8
        invoice.shipping_extax = invoice.shipping_fee - invoice.tax10
        invoice.final_price = invoice.total_price + invoice.shipping_fee
        invoice.final_tax = invoice.tax8 + invoice.tax10
        invoice.final_extax = invoice.final_price - invoice.final_tax

        invoice.save()

        items.update(invoice_id=invoice)
    
    return render(request, 'orders/gyoumu.html')

def gyoumu_menu(request):
    return render(request, 'orders/gyoumu.html')