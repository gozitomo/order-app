from django.core.mail import send_mail
from django.conf import settings
from email.utils import formataddr
from .models import MailTemplate

from .models import MailTemplate

def sendmail(order, template):
    """
    注文情報をメール送信
    """

    subject = f"""{template.subject}（注文番号：{order.order_id}）"""
    base_sign = MailTemplate.objects.filter(key="base_sign").first()
    message = f"""
    {template.body}
    【注文番号】{order.order_id}
    【注文者】{order.user.userprofile.company_name}
    【納品予定日】{order.product_delivery_date.date.strftime("%Y/%m/%d")}

    【注文内容】
    """
    for item in order.items.all():
        message += f"{item.product.name}:{item.price_table.unit}@{item.price_table.price}×{item.quantity}\n"
    message += f"【合計金額】{order.final_price}円（別途送料{order.shipping_price}円）\n"
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