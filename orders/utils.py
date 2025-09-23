from typing import Optional, Sequence

from django.contrib.auth import get_user_model

from users.models import UserProfile

from .models import ShippingFeeRule, ShippingRegion


def _resolve_shipping_region(user_or_profile) -> Optional[ShippingRegion]:
    """Extract the shipping region from a user or profile instance."""
    if user_or_profile is None:
        return None

    if isinstance(user_or_profile, ShippingRegion):
        return user_or_profile

    if isinstance(user_or_profile, UserProfile):
        return user_or_profile.region

    user_model = get_user_model()
    if isinstance(user_or_profile, user_model):
        profile = getattr(user_or_profile, "userprofile", None)
        return getattr(profile, "region", None)

    # Fallback for objects that expose a userprofile attribute (e.g. mock objects)
    profile = getattr(user_or_profile, "userprofile", None)
    return getattr(profile, "region", None)


def calculate_shipping_fee(user_or_profile, weights: Sequence[int], cool_flg: bool) -> Optional[int]:
    region = _resolve_shipping_region(user_or_profile)

    if region is None:
        return None

    if not weights:
        return 0

    max_weight = 15 if cool_flg else 20
    max_box = 3  # 1口にできる箱数

    chunks = []
    chunk_weight = 0
    box_cnt = 0

    for weight in weights:
        # 1つ追加して条件を超えるなら、新しいチャンクを開始
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
            raise ValueError("送料ルールが見つかりません")
        total_fee += rule.shipping_fee

    return total_fee
