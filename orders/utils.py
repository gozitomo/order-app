from .models import ShippingFeeRule

def calculate_shipping_fee(quantity):
    rule = ShippingFeeRule.objects.filter(
        min_qty__lte=quantity,
        max_qty__gte=quantity,
    ).first()

    if rule:
        return rule.fee
    return 0 #該当しない場合は送料無料
    