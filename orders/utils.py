from .models import ShippingFeeRule

def calculate_shipping_fee(region, total_weight, cool_flg):
    rule = ShippingFeeRule.objects.filter(
        name=region,
        cool_flg=cool_flg,
        min_weight__lt=total_weight,
        max_weight__gte=total_weight,
    ).first()
    print(rule.shipping_fee)

    if rule:
        return rule.shipping_fee
    return 0 #該当しない場合は送料無料
    