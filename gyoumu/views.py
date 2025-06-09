from io import TextIOWrapper
import csv

from django.apps import apps
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponse
from django.utils.timezone import localdate, now

from orders.models import Order, OrderItem, Invoice
from products.models import FruitKind, ProductName, PriceTable, ProductDeliveryDate
from sitecontent.models import OrderNote, OrderHistoryNote
from users.models import UserProfile, UserGroup
from users.models import UserProfile
from users.models import User
from sitecontent.models import MailTemplate
from sitecontent.utils import sendmail

# Create decorators

def admin_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)

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
        elif field_type == 'DateField':
            return datetime.strptime(value, '%Y-%m-%d').date()
        elif field_type == 'DateTimeField':
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        elif field_type == 'DecimalField':
            return field.to_python(value)  # Decimal型を正確に
        elif field_type in ('ForeignKey', 'OneToOneField'):
            rel_model = field.remote_field.model
            # モデルごとに解決キーを切り替える
            lookup_field = {
                'User': 'username',
                'ShippingRegion': 'name',
                'UserGroup': 'name',
                'FruitKind': 'name',
            }.get(rel_model.__name__, 'name')
            return rel_model.objects.get(**{lookup_field: value})  # ← name以外にしたければ調整
        else:
            return value  # TextField, CharField, etc.
    except Exception as e:
        raise ValueError(f"{field.name} の変換エラー: {e}")

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
                print(f"\n--- 処理中の行 {created_count}: {row}")
                data = {}
                for field_name, raw_value in zip(field_names, row):
                    print(f"{field_name=}, {raw_value=}")  # デバッグ出力
                    field = fields.get(field_name)
                    if not field:
                        continue #不明なカラムは無視
                    data[field_name] = parse_field_value(field, raw_value)

                print(f"  処理後のデータ: {data}")


                if model.__name__ == 'User':
                    raw_password = data.pop('password', None)
                    obj = model(**data)
                    if raw_password:
                        print("ハッシュ化します")
                        obj.set_password(raw_password) #ハッシュ化
                    obj.save()
                else:
                    unique_keys = ['user'] if model.__name__  == 'UserProfile' else[]
                    if unique_keys:
                        lookup = {k: data[k] for k in unique_keys}
                        defaults = {k: v for k, v in data.items() if k not in unique_keys}
                        obj, created = model.objects.update_or_create(**lookup, defaults=defaults)
                    else:
                        model.objects.create(**data)
                created_count += 1
            except Exception as e:
                messages.error(request, f"{created_count}行の処理中にエラー: {e}")
                continue

        messages.success(request, f"{created_count}件の{model_name}データを登録しました。")
        return redirect('csv_upload')

    return render(request, 'gyoumu/csv_uploader.html')

@admin_required
def export_model_csv(request, app_label=None, model_name=None):

    if request.method == 'POST' and (app_label==None or model_name==None):
        app_label = request.POST.get('app_label')
        model_name = request.POST.get('model_name')
        Model = apps.get_model(app_label, model_name)
        objects = Model.objects.all()
        if not objects.exists():
            return HttpResponse("No data available", content_type="text/plain")

        #csvレスポンス設定
        response = HttpResponse(content_type="text/csv")
        response['Content-Disposition'] = f'attachment; filename="{app_label}.{model_name}.csv"'

        #フィールド名取得
        field_names = [field.name for field in Model._meta.fields]

        writer = csv.writer(response)
        writer.writerow(field_names)

        for obj in objects:
            row = [getattr(obj, field) for field in field_names]
            writer.writerow(row)
        
        return response

    return render(request, 'gyoumu/export_model_csv.html')

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
    return render(request, 'gyoumu/gyoumu.html')


@admin_required
def order_confirm(request, order_id=None):
    if request.method == 'POST' and order_id is not None:
        order = get_object_or_404(Order, order_id=order_id)
        order.status = 'received'
        order.save()

        template = MailTemplate.objects.filter(key="order_confirm").first()

        try:
            sendmail(order, template)
        except Exception as e:
            print("メール送信エラー：", e)

        return redirect('order_confirm')

    orders = Order.objects.filter(
        total_weight__gt=0).prefetch_related('items').order_by('product_delivery_date')
    today = localdate()
    notes = OrderHistoryNote.objects.all()

    for order in orders:

        #本日注文分でなければ、#納品日まで10日を切ったらキャンセル不可とする
        if  order.product_delivery_date and (order.product_delivery_date.date - today).days < 3 and order.created_at.date()!=today:
            order.status = 'preparing'
            order.save()
        order.userprofile = getattr(order.user, 'userprofile', None)

    return render(request, 'gyoumu/order_confirm.html', {
        'orders': orders,
        'notes': notes,
        })
