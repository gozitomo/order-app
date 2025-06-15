from io import TextIOWrapper
import csv
from collections import defaultdict
from datetime import date

from django.apps import apps
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponse
from django.utils.timezone import localdate, now
from django.db.models import Sum, Q, Prefetch, Min, Max, F
from django.db.models.functions import Coalesce

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
def bulk_delinote_export(request):
    today = date(2025,7,7)
    users = User.objects.all()
    all_summaries = []
    response = None

    print(today)

    for user in users:

        print(user)

        orders = Order.objects.filter(
            user=user,
            deli_note_id__isnull=True,
            product_delivery_date__isnull=False,
            product_delivery_date__date=today,
            status="preparing",
        ).prefetch_related('items')

        if not orders.exists():
            print("orderなし")
            continue

        summary = {
                'items': defaultdict(lambda: {'quantity': 0}),
                'tax8_price': 0,
                'tax10_price': 0,
                'total_weight': 0,
                'shipping_price': 0,
                'final_price': 0,
                'orders': [],
                'user': user,
                'delivery_date': today,
            }


        for order in orders:
            summary['tax8_price'] += order.tax8_price or 0
            summary['tax10_price'] += order.tax10_price or 0
            summary['total_weight'] += order.total_weight or 0
            summary['shipping_price'] += order.shipping_price or 0
            summary['final_price'] += order.final_price or 0
            summary['orders'].append(order)

            print(summary)

            for item in order.items.all():
                pt_key = item.price_table.id
                summary['items'][pt_key]['quantity'] += item.quantity
                summary['items'][pt_key]['item'] = item

                print(summary)

        #まとめたアイテムをリストに変換して格納
        for pt_id, data in summary['items'].items():
            item = data['item']
            pt = item.price_table
            product = item.product
            total_qty = data['quantity']
            
            all_summaries.append({
                'user': summary['user'],
                'delivery_date': summary['delivery_date'],
                'product': product,
                'grade': pt.grade,
                'size': pt.size,
                'unit': pt.unit,
                'price': pt.price,
                'quantity': total_qty,
                'tax10_flg': pt.tax10_flg,
                'tax8_price': summary['tax8_price'],
                'tax10_price': summary['tax10_price'],
                'total_weight': summary['total_weight'],
                'shipping_price': summary['shipping_price'],
                'final_price': summary['final_price'],
            })

            response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
            response['Content-Disposition'] = f'attachment; filename="納品書_{today}.csv'

            writer = csv.writer(response)
            writer.writerow([
                "csv_type(変更不可)","行形式","取引先名称","件名","納品日","納品書番号","メモ","タグ","小計","消費税","源泉徴収税","合計金額","取引先敬称","取引先郵便番号","取引先都道府県","取引先住所1","取引先住所2","取引先部署","取引先担当者役職","取引先担当者氏名","自社担当者氏名","備考","納品ステータス","メール送信ステータス","郵送ステータス","ダウンロードステータス","品名","品目コード","単価","数量","単位","詳細","金額","源泉徴収","品目消費税率"
            ])

            for row in all_summaries:
                user = row["user"]
                row_cnt = 0
                if user != row["user"]:
                    row_cnt = 0

                if row_cnt == 0:
                    writer.writerow([
                        "40201",
                        "納品書",
                        row["user"],
                        row["delivery_date"],
                        '1',
                        "",
                        "",
                        row["final_price"] / 1.08,
                        row["final_price"] / 1.08 * 0.08,
                        "",
                        row["final_price"],""
                        ,"","","","","","","","","","","","",""
                    ])
                else:
                    writer.writerow([
                        "40201",
                        "品目",
                        "","","","","","","","","","","","","","","","","","","","","","","","",
                        "品目A","",
                        row["price"],
                        row["quantity"],"","",
                        row["price"] * row["quantity"],"",
                        "軽8%"
                    ])
                row_cnt += 1

    if response:
        print(all_summaries)
    else:
        response = HttpResponse("NG")

    return response


    #     deli_note = DeliNote.objects.create(
    #         user = user,
    #         deli_note_id = Invoice.generate_invoice_number(),
    #         issued_date = today,
    #         period_start = first_day_last_month,
    #         period_end = last_day_last_month,
    #         total_price = sum(item.subtotal for item in items),
    #         tax8 = sum(item.tax for item in items),
    #         shipping_fee = sum(item.shipping_fee for item in items),
    #         tax10 = sum(item.shipping_tax for item in items),
    #         total_extax = 0,
    #         shipping_extax = 0,
    #         final_price = 0,
    #         final_tax = 0,
    #         final_extax = 0,
    #     )
    #     invoice.total_extax = invoice.total_price - invoice.tax8
    #     invoice.shipping_extax = invoice.shipping_fee - invoice.tax10
    #     invoice.final_price = invoice.total_price + invoice.shipping_fee
    #     invoice.final_tax = invoice.tax8 + invoice.tax10
    #     invoice.final_extax = invoice.final_price - invoice.final_tax

    #     invoice.save()

    #     items.update(invoice_id=invoice)
    
    # return render(request, 'csv_upload')


@admin_required
def gyoumu_menu(request):
    return render(request, 'gyoumu/gyoumu.html')


