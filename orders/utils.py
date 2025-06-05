from .models import ShippingFeeRule

def calculate_shipping_fee(region, weights, cool_flg):
    max_weight = 15 if cool_flg else 20
    max_box = 3 #1口にできる箱数

    chunks = []
    chunk_weight = 0
    box_cnt = 0

    for weight in weights:
        #1つ追加して条件を超えるなら、新しいチャンクを開始
        if (chunk_weight + weight > max_weight) or (box_cnt + 1 > max_box):
            chunks.append(chunk_weight)
            chunk_weight = weight
            box_cnt = 1
        else:
            chunk_weight += weight
            box_cnt += 1

    if chunk_weight > 0:
        chunks.append(chunk_weight)

    total_fee = 0
    for chunk in chunks:
        rule = ShippingFeeRule.objects.filter(
            region=region,
            cool_flg=cool_flg,
            min_weight__lt=chunk,
            max_weight__gte=chunk,
        ).first()

        if not rule:
            raise ValueError(f"送料ルールが見つかりません")
        print(rule.shipping_fee)
        total_fee += rule.shipping_fee
        
    return total_fee