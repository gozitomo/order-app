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

def parse_field_value(field, value):
    field_type = field.get_internal_type()

    if value == '' and not field.null:
        return None

    try:
        if field_type == 'BooleanField':
            return value.lower() in ('true', '1', 'yes', 'y', 't')
        elif field_type in ('IntegerField', 'PositiveIntegerField'):
            return int(value)
        elif field_type == 'FloatField':
            return float(value)
        elif field_type == 'DecimalField':
            return field.to_python(value)  # Decimal型を正確に
        elif field_type == 'ForeignKey':
            rel_model = field.remote_field.model
            return rel_model.objects.get(name=value)  # ← name以外にしたければ調整
        else:
            return value  # TextField, CharField, etc.
    except Exception as e:
        raise ValueError(f"{field.name} の変換エラー: {e}")

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
    kinds = FruitKind.objects.all().order_by('id')
    products = ProductName.objects.select_related('kind').all().order_by('-sort_no')
    return render(request, 'orders/neworder_top.html', {
        'kinds': kinds,
        'products': products
        })

@login_required
def order_history(request):
    orders = Order.objects.filter(
        user=request.user,
        total_weight__gt=0).prefetch_related('items').order_by('product_delivery_date')
    today = localdate()

    for order in orders:

        #本日注文分でなければ、#納品日まで10日を切ったらキャンセル不可とする
        if  order.product_delivery_date and (order.product_delivery_date.date - today).days < 3 and order.created_at.date()!=today:
            order.status = 'preparing'
            order.save()

    return render(request, 'orders/order_history.html', {
        'orders': orders,
        })

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {
        'order': order,
        })


def sendmail(order, subject):
    """
    注文情報をメール送信
    """

    print(order.id)
    print(subject)


    message = f"""
    【注文ID】{order.id}
    【注文者】{order.user.userprofile.company_name}
    【納品予定日】{order.product_delivery_date.date.strftime}

    【注文内容】
    """
    for item in order.items.all():
        message += f"-{item.product.name}:{item.price_table.unit}@{item.price_table.price}×{item.quantity}/n"
    message += f"/n【合計金額】{order.final_price}円（うち送料{order.shipping_price}円）/n"

    print(message)

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
        fail_silently=False
    )


@login_required
def order_change(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    user_profile = getattr(request.user, 'userprofile', None)
    user_group = getattr(user_profile, 'user_group', None)
    user_region = getattr(user_profile, 'region', None)
    today = localdate()
    item = order.items.first()
    try:
        product = item.product
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
            cool_flg = request.POST.get(f'cool_flg') == "true"
            delivery_id = request.POST.get(f'delivery_date')
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
            #order.remarks = remarks
            order.save()

            try:
                sendmail(order, subject="【注文変更確定（仮注文）】ご注文内容を変更しました")
            except Exception as e:
                print('メール送信エラー：', e)

            return redirect('order_detail', order_id=order.id)
        
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
        #remarks = request.POST.get(f'remarks')


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
        #order.remarks = remarks
        order.save()

        print('注文保存完了、メールを送ります')

        sendmail(order, subject="【仮注文確定】ご注文ありがとうございます")


        return redirect('order_detail', order_id = order.id)
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
    response['Content-Disposition'] = f'filename="invoice_{order.id}.pdf"'
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
def upload_generic_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        decoded_file = TextIOWrapper(csv_file, encoding='utf-8')
        reader = csv.reader(decoded_file)
        rows = list(reader)

        if not rows or len(rows) < 3:
            messages.error(request, "CSV形式が不正です（最低3行必要です）")
            return redirect('csv_upload')

        raw_model_name = rows[0][0].strip()
        try:
            if '.' in raw_model_name:
                app_label, model_name = raw_model_name.split('.')
            else:
                messages.error(request, "モデル名は'アプリ名.モデル名'の形式で指定してください")
                return redirect('csv_upload')

            model = apps.get_model(app_label, model_name)
        except LookupError:
            messages.error(request, f"モデル'{model_name}'が見つかりません。")
            return redirect('csv_upload')

        field_names = [f.strip() for f in rows[1]]
        created_count = 0
        fields = {f.name: f for f in model._meta.get_fields() if not f.auto_created}

        for row in rows[2:]:
            try:
                data = {}
                for field_name, raw_value in zip(field_names, row):
                    field = fields.get(field_name)
                    if not field:
                        continue #不明なカラムは無視
                    data[field_name] = parse_field_value(field, raw_value)
                model.objects.create(**data)
                created_count += 1
            except Exception as e:
                messages.error(request, f"{created_count}行の処理中にエラー: {e}")
                continue

        messages.success(request, f"{created_count}件の{model_name}データを登録しました。")
        return redirect('csv_upload')

    return render(request, 'orders/csv_uploader.html')


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
    
    return render(request, 'csv_upload')


@admin_required
def gyoumu_menu(request):
    return render(request, 'orders/gyoumu.html')
