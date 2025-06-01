from datetime import date, timedelta, datetime
from io import TextIOWrapper
from django.apps import apps
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.serializers.json import DjangoJSONEncoder
from django.core.mail import send_mail
from django.conf import settings
from django.db import models
from django.db.models import Sum, Q
from django.views.decorators.http import require_POST
from django.utils.timezone import localdate, now
from email.utils import formataddr
from .models import Order, OrderItem, Invoice
from products.models import FruitKind, ProductName, PriceTable, ProductDeliveryDate
from sitecontent.models import OrderNote, OrderHistoryNote
from users.models import UserProfile, UserGroup
from users.models import UserProfile
from users.models import User
from .utils import calculate_shipping_fee

from weasyprint import HTML
import json

# Create decorators

def admin_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)

# Create your views here.

@login_required
def order_top(request):
    kinds = FruitKind.objects.all().order_by('id')
    products = ProductName.objects.select_related('kind').all().order_by('-sort_no')
    notes = OrderNote.objects.all()
    return render(request, 'orders/neworder_top.html', {
        'kinds': kinds,
        'products': products,
        'notes': notes
        })

@login_required
def order_history(request):
    orders = Order.objects.filter(
        user=request.user,
        total_weight__gt=0).prefetch_related('items').order_by('product_delivery_date')
    today = localdate()
    notes = OrderHistoryNote.objects.all()

    for order in orders:

        #本日注文分でなければ、#納品日まで10日を切ったらキャンセル不可とする
        if  order.product_delivery_date and (order.product_delivery_date.date - today).days < 3 and order.created_at.date()!=today:
            order.status = 'preparing'
            order.save()

    return render(request, 'orders/order_history.html', {
        'orders': orders,
        'notes': notes
        })

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {
        'order': order,
        })


def sendmail(order, subject):
    """
    注文情報をメール送信
    """

    print(order.order_id)
    print(subject)


    message = f"""
    【注文番号】{order.order_id}
    【注文者】{order.user.userprofile.company_name}
    【納品予定日】{order.product_delivery_date.date.strftime}

    【注文内容】
    """
    for item in order.items.all():
        message += f"-{item.product.name}:{item.price_table.unit}@{item.price_table.price}×{item.quantity}/n"
    message += f"/n【合計金額】{order.final_price}円（うち送料{order.shipping_price}円）/n"

    print(message)
    from_email = formataddr(("プログレスファーム（B2B発注アプリ）", settings.DEFAULT_FROM_EMAIL))
    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=[order.user.email],
        fail_silently=False
    )


@login_required
def order_change(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    user_profile = getattr(request.user, 'userprofile', None)
    user_group = getattr(user_profile, 'user_group', None)
    user_region = getattr(user_profile, 'region', None)
    today = localdate()
    item = order.items.first()
    try:
        product = item.product
        options = product.kind.options.filter(
            Q(user_group=user_group) | Q(user_group__name='Forall'),
            status='available'
        )

        #価格テーブルを定義
        price_data = list(options.values('grade', 'size', 'unit', 'weight', 'price', 'tax10_flg'))
        unique_grades = options.values_list('grade', flat=True).distinct()
        grades_data = list(unique_grades)
        unique_sizes = options.values_list('size', flat=True).distinct()
        sizes_data = list(unique_sizes)
        unique_units = options.values_list('unit', flat=True).distinct()
        units_data = list(unique_units)

        delivery_dates_raw = ProductDeliveryDate.objects.filter(product=product).order_by('date')

        delivery_dates = [
            {
                'value': date.id,
                'label': date.date.strftime('%Y年%m月%d日')
            }
            for date in delivery_dates_raw
        ]

        if request.method == 'POST':
            cool_flg = request.POST.get(f'cool_flg') == "true"
            delivery_id = request.POST.get(f'delivery_date')
            remarks = request.POST.get(f'remarks')
            delivery_date_obj = get_object_or_404(ProductDeliveryDate, id=delivery_id)

            tax8_price = 0
            tax10_price = 0
            total_weight = 0
            shipping_price = 0
            shipping_tax = 0
            final_price = 0
            quantity = 0
            subtotal = 0

            for item in order.items.all():
                new_qty = request.POST.get(f'quantity_{item.id}')

                if new_qty is not None:
                    try:
                        qty = int(new_qty)
                        if qty == 0:
                            item.delete()
                            continue
                        
                        item.quantity = qty
                        item.subtotal = item.price_table.price * item.quantity
                        total_weight += item.price_table.weight * item.quantity
                        item.save()

                        if item.price_table.tax10_flg:
                            tax10_price += item.subtotal
                        else:
                            tax8_price += item.subtotal

                    except ValueError:
                        pass
            
            i = 0
            while True:
                qty = request.POST.get(f'quantity_{i}')
                if not qty:
                    break
                if int(qty) == 0:
                    i += 1
                    continue
                
                grade = request.POST.get(f'grade_{i}')
                size = request.POST.get(f'size_{i}')
                unit = request.POST.get(f'unit_{i}')

                if int(qty)>0:
                    quantity = int(qty)
                    option = options.filter(grade=grade, size=size, unit=unit).first()
                    if option:
                        weight = option.weight * quantity
                        total_weight += weight
                        subtotal = option.price * quantity

                        if option.tax10_flg:
                            tax10_price += subtotal

                        else:
                            tax8_price += subtotal

                        OrderItem.objects.create(
                            order=order,
                            price_table=option,
                            product=product,
                            quantity=quantity,
                            subtotal=subtotal,                            
                        )
                i += 1

            order.product_delivery_date=delivery_date_obj
            order.tax8_price = tax8_price
            order.tax8 = tax8_price / 1.08 * 0.08
            order.tax10_price = tax10_price
            order.tax10 = tax10_price / 1.1 * 0.1
            order.total_weight = total_weight
            order.cool_flg = cool_flg
            order.shipping_price = calculate_shipping_fee(user_region, total_weight, cool_flg)
            order.shipping_tax = order.shipping_price / 1.1 * 0.1
            order.final_price = order.tax8_price + order.tax10_price + order.shipping_price
            order.status = 'tentative'
            order.remarks = remarks
            order.save()

            try:
                sendmail(order, subject="【注文変更確定（仮注文）】ご注文内容を変更しました")
            except Exception as e:
                print('メール送信エラー：', e)

            return redirect('order_detail', order_id=order.order_id)
        
    except Exception as e:
        message = ''
        return_url = ''
        return render(request, 'orders/order_error.html', {
            'message' : 'エラーが発生しました。園主までお問い合わせください',
            'return_url' : 'order_history'
        })


    return render(request, 'orders/order_change.html', {
        'product': product,
        'price_data_json': json.dumps(price_data, cls=DjangoJSONEncoder),
        'grades': grades_data,
        'sizes': sizes_data,
        'units': units_data,
        'delivery_dates': delivery_dates,
        'order': order,
    })

@login_required
def neworder(request, product_id):
    product = get_object_or_404(ProductName, id=product_id)
    user_profile = getattr(request.user, 'userprofile', None)
    user_group = getattr(user_profile, 'user_group', None)
    user_region = getattr(user_profile, 'region', None)
    options = product.kind.options.filter(
        Q(user_group=user_group) | Q(user_group__name='Forall')
    )

    #価格テーブルを定義
    price_data = list(options.values('grade', 'size', 'unit', 'weight', 'price', 'tax10_flg'))
    unique_grades = options.values_list('grade', flat=True).distinct()
    grades_data = list(unique_grades)
    unique_sizes = options.values_list('size', flat=True).distinct()
    sizes_data = list(unique_sizes)
    unique_units = options.values_list('unit', flat=True).distinct()
    units_data = list(unique_units)
    delivery_dates_raw = ProductDeliveryDate.objects.filter(product=product).order_by('date')

    delivery_dates = [
        {
            'value': date.id,
            'label': date.date.strftime('%Y年%m月%d日')
        }
        for date in delivery_dates_raw
    ]

    if request.method == 'POST':
        #新しい注文を作成
        order = Order.objects.create(user=request.user)
        cool_flg = request.POST.get(f'cool_flg') == "true"

        tax8_price = 0
        tax8 = 0
        tax10_price = 0
        tax10 = 0
        total_weight = 0
        shipping_price = 0
        shipping_tax = 0
        final_price = 0
        quantity = 0
        subtotal = 0

        delivery_id = request.POST.get(f'delivery_date')
        delivery_date_obj = get_object_or_404(ProductDeliveryDate, id=delivery_id)
        remarks = request.POST.get(f'remarks')


        i = 0
        while True:
            qty = request.POST.get(f'quantity_{i}')
            if not qty:
                break
            if int(qty) == 0:
                i += 1
                continue

            grade = request.POST.get(f'grade_{i}')
            size = request.POST.get(f'size_{i}')
            unit = request.POST.get(f'unit_{i}')


            if int(qty) > 0:
                quantity = int(qty)
                option = options.filter(grade=grade, size=size, unit=unit).first()
                if option:
                    weight = option.weight * quantity
                    total_weight += weight
                    subtotal = option.price * quantity

                    if option.tax10_flg:
                        tax10_price += subtotal

                    else:
                        tax8_price += subtotal

                    OrderItem.objects.create(
                        order=order,
                        price_table=option,
                        product=product,
                        quantity=quantity,
                        subtotal=subtotal,
                    )
            i += 1


        order.product_delivery_date=delivery_date_obj
        order.tax8_price = tax8_price
        order.tax8 = tax8_price / 1.08 * 0.08
        order.tax10_price = tax10_price
        order.tax10 = tax10_price / 1.1 * 0.1
        order.total_weight = total_weight
        order.cool_flg = cool_flg
        order.shipping_price = calculate_shipping_fee(user_region, total_weight, cool_flg)
        order.shipping_tax = shipping_price / 1.1 * 0.1
        order.final_price = order.tax8_price + order.tax10_price + order.shipping_price
        order.remarks = remarks
        order.save()

        print('注文保存完了、メールを送ります')

        sendmail(order, subject="【仮注文確定】ご注文ありがとうございます")


        return redirect('order_detail', order_id = order.order_id)
        #リダイレクト先は注文確認画面
        #return redirect('order_history')
    
        # Prepare pricing data for JavaScript

    return render(request, 'orders/neworder_1.html', {
        'product': product,
        'price_data_json': json.dumps(price_data, cls=DjangoJSONEncoder),
        'grades': grades_data,
        'sizes': sizes_data,
        'units': units_data,
        'delivery_dates': delivery_dates,
        })


@login_required
def order_invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    html_string = render_to_string('orders/invoice_pdf.html', {'order': order})
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="invoice_{order.order_id}.pdf"'
    return response


@login_required
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


@login_required
def my_invoices(request):
    invoices = Invoice.objects.filter(user=request.user).order_by('-issued_date')
    return render(request, 'orders/my_invoice_list.html', {'invoices': invoices})

@login_required
@require_POST
def order_cancel(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    if order.status == 'キャンセル':
        messages.info(request, "すでにキャンセル済みです。")
    elif order.status == 'キャンセル不可':
        messages.error(request, "この注文は当日以外キャンセルできません。/n Lineまたはお電話にてお問い合わせくださいませ。")
    else:
        order.status = 'キャンセル'
        order.save()
        messages.success(request, "注文をキャンセルしました。")

    #リダイレクト先は注文詳細
    return redirect('order_detail', order_id=order.order_id)

