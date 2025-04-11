from .models import ShippingFeeRule

def calculate_sipping_fee(total_quantity):
    rule = ShippingFeeRule.objects.filter(
        min_qty__lte=total_quantity,
        max_qty__gte=total_quantity,
    ).first()

    if rule:
        return rule.fee
    return 0 #該当しない場合は送料無料
    