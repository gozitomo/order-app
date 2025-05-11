from datetime import date, timedelta, datetime
from io import TextIOWrapper
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum, Q
from django.views.decorators.http import require_POST
from django.utils.timezone import localdate, now
from .models import Order, OrderItem, Invoice
from products.models import FruitKind, ProductName, PriceTable, ProductDeliveryDate
from users.models import UserProfile, UserGroup
from users.models import UserProfile
from users.models import User
from .utils import calculate_shipping_fee
from .forms import CustomSignupForm
from weasyprint import HTML
import json
import csv

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
def order_top(request):
    products = ProductName.objects.select_related('kind').all().order_by('kind__name', 'name')
    return render(request, 'orders/neworder_top.html', {'products': products})


def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('delivery_date')
    today = localdate()

    print(orders)

    for order in orders:

        #本日注文分でなければ、#納品日まで10日を切ったらキャンセル不可とする
        if  order.delivery_date and (order.delivery_date - today).days < 10 and order.created_at.date()!=today:
            order.status = 'キャンセル不可'
            order.save()

    return render(request, 'orders/order_history.html', {
        'orders': orders,
        })

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {
        'order': order,
        })

def order_change(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    today = localdate()
    item = order.items.first()
    product = item.product
    delivery_dates_raw = list(product.available_dates.values_list('date', flat=True).distinct())
    

    delivery_dates = [
        {
            'value': date.strftime('%Y-%m-%d'),
            'label': date.strftime('%Y年%m月%d日')
        }
        for date in delivery_dates_raw
    ]

    #納品日まで10日を切ったら編集不可
    if order.delivery_date and (order.delivery_date - today).days < 10:
        return render(request, 'orders/order_error.html', {
            'message': 'ご注文内容の変更は納品希望日の10日前までにお願いいたします。',
            'return_url': reverse('order_detail', args=[order.id])
            })

    if request.method == 'POST':
        for item in order.items.all():
            new_qty = request.POST.get(f'quantity_{item.id}')
            if new_qty is not None:
                try:
                    item.quantity = int(new_qty)
                    item.subtotal = item.price * item.quantity
                    item.save()
                except ValueError:
                    pass
        order.total_price = sum(i.subtotal for i in order.items.all())
        order.save()
        return redirect('order_history', order_id=order.id)

    return render(request, 'orders/order_change.html', {
        'order': order,
        'delivery_dates': delivery_dates,
    })

def neworder(request, product_id):
    product = get_object_or_404(ProductName, id=product_id)
    delivery_date = product.available_dates.all()
    user_profile = getattr(request.user, 'userprofile', None)
    user_group = getattr(user_profile, 'user_group', None)
    options = product.kind.options.filter(
        Q(user_group=user_group) | Q(user_group__name='Forall')
    )

    #価格テーブルを定義
    price_data = list(options.values('grade', 'size', 'amount', 'price', 'unit'))
    unique_grades = options.values_list('grade', flat=True).distinct()
    grades_data = list(unique_grades)
    unique_sizes = options.values_list('size', flat=True).distinct()
    sizes_data = list(unique_sizes)
    unique_amounts = options.values_list('amount', flat=True).distinct()
    amounts_data = list(unique_amounts)
    delivery_dates_raw = list(delivery_date.values_list('date', flat=True).distinct())

    delivery_dates = [
        {
            'value': date.strftime('%Y-%m-%d'),
            'label': date.strftime('%Y年%m月%d日')
        }
        for date in delivery_dates_raw
    ]

    if request.method == 'POST':
        #新しい注文を作成
        order = Order.objects.create(user=request.user)

        total_quantity = 0
        total_amount = 0
        total_price = 0
        tax = 0
        total_tax = 0
        total_shipping_fee = 0
        subtotal = 0
        price = 0
        quantity = 0

        delivery_str = request.POST.get(f'delivery_date')
        delivery = datetime.strptime(delivery_str, '%Y-%m-%d').date()
        print(delivery)

        i = 0
        while True:
            qty = request.POST.get(f'quantity_{i}')
            if not qty:
                break

            grade = request.POST.get(f'grade_{i}')
            size = request.POST.get(f'size_{i}')
            amount = request.POST.get(f'amount_{i}')


            if int(qty) > 0:
                quantity = int(qty)
                option = options.filter(grade=grade, size=size, amount=amount).first()
                if option:
                    amount = int(option.amount.replace('kg', ''))
                    subtotal = option.price * quantity
                    total_price += subtotal
                    unit = option.unit
                    # shipping_fee = calculate_shipping_fee(quantity)
                    # shipping_tax = shipping_fee / 1.1 * 0.1
                    # total_shipping_fee += shipping_fee
                    # total_shipping_tax = total_shipping_fee / 1.1 * 0.1
                    # tax = subtotal / 1.08 * 0.08
                    # total_tax += tax
                    # total_quantity += quantity * amt

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        grade=grade,
                        size=size,
                        amount=amount,
                        price=option.price,
                        quantity=quantity,
                        subtotal=subtotal,
                        unit=unit,
                        # shipping_fee = shipping_fee,
                        # tax = tax,
                        # shipping_tax = shipping_tax,
                    )
            i += 1

        # order.total_quantity = total_quantity
        order.total_price = total_price
        order.delivery_date=delivery
        # order.total_shipping_fee = total_shipping_fee
        # order.shipping_tax = total_shipping_tax
        # order.final_total = order.total_price + order.total_shipping_fee
        # order.total_tax = total_tax
        order.save()

        return redirect('order_detail', order_id = order.id)
        #リダイレクト先は注文確認画面
        #return redirect('order_history')
    
        # Prepare pricing data for JavaScript

    return render(request, 'orders/neworder_1.html', {
        'product': product,
        'price_data_json': json.dumps(price_data, cls=DjangoJSONEncoder),
        'grades': grades_data,
        'sizes': sizes_data,
        'amounts': amounts_data,
        'delivery_dates': delivery_dates,
        })


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
def order_cancel(request, order_id):
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
def upload_pricetable(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        decoded_file = TextIOWrapper(csv_file, encoding='utf-8')
        reader = csv.DictReader(decoded_file)

        for row in reader:
            print(row)
            try:
                kind = FruitKind.objects.get(name=row['kind'])
                user_group = UserGroup.objects.get(name=row['user_group'])
                PriceTable.objects.create(
                    kind=kind,
                    grade=row['grade'],
                    size=row['size'],
                    amount=row['amount'],
                    unit=row['unit'],
                    price=row['price'],
                    user_group=user_group
                )
            except Exception as e:
                messages.error(request, f"アップロードエラー: {e}")
                continue

        messages.success(request, "アップロードが完了しました。")
        return redirect('gyoumu_menu')

    return render(request, 'orders/upload_pricetable.html')


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