from textwrap import dedent
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from email.utils import formataddr
from .models import MailTemplate

def sendmail(order, template):
    """
    注文情報をメール送信
    """

    subject = f"""{template.subject}（注文番号：{order.order_id}）"""
    base_sign = MailTemplate.objects.filter(key="base_sign").first()
    item = order.items.filter(quantity__gt=0).first()

    product_name = item.product
    if order.pickup_flg:
        mail_kbn = "引取り"
    elif order.cool_flg:
        mail_kbn = "冷蔵便"
    else:
        mail_kbn = "通常便"

    message = dedent(f"""
{template.body}

【お客様名】{order.user.userprofile.company_name}
【注文番号】{order.order_id}
【発送見込】{order.product_delivery_date.date.strftime("%Y/%m/%d")}
【注文内容】{product_name}（{item.product.kind}）・{mail_kbn}
""")
    for i in order.items.all():
        message += dedent(f"　　　　　　{item.price_table.grade}　{item.price_table.unit}@{item.price_table.price|intcomma}×{item.quantity}\n")
    message += dedent(f"【特記事項】{order.remarks}\n")
    message += dedent(f"【合計金額】{order.final_price|intcomma}円（別途送料{order.shipping_price|intcomma}円）\n\r\n")
    message += base_sign.body
    

    print(message)
    from_email = formataddr(("プログレスファーム（B2B発注アプリ）", settings.DEFAULT_FROM_EMAIL))
    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=[order.user.email, from_email],
        fail_silently=False
    )