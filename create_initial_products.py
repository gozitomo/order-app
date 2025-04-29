import os
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# Import your Product model
from products.models import FruitKind, ProductName, PriceTable, ProductDeliveryDate

def run():
    # Create fruits
    peach = FruitKind.objects.get_or_create(name="桃")[0]
    plum = FruitKind.objects.get_or_create(name="プラム")[0]

    # Create product names
    akatsuki = ProductName.objects.get_or_create(kind=peach, name="あかつき", description="7月末〜8月頭頃に発送となります")[0]
    natsukko = ProductName.objects.get_or_create(kind=peach, name="なつっこ", description="8月末〜8月10日頃に発送となります")[0]
    ooishiwase = ProductName.objects.get_or_create(kind=plum, name="大石早生", description="7月頭〜中旬頃に発送となります")[0]
    sorudamu = ProductName.objects.get_or_create(kind=plum, name="ソルダム", description="7月下旬〜7月末頃に発送となります")[0]

    # Create pricetable
    pricetable = [
        {"kind": peach, "grade": "秀", "size": "LL", "amount": "5kg", "price": 5000, "unit": "箱"},
        {"kind": peach,  "grade": "秀", "size": "L", "amount": "5kg", "price": 5000, "unit": "箱"},
        {"kind": peach,  "grade": "秀", "size": "M", "amount": "5kg", "price": 4400, "unit": "箱"},
        {"kind": peach,  "grade": "優", "size": "LL", "amount": "5kg", "price": 4200, "unit": "箱"},
        {"kind": peach,  "grade": "優", "size": "L", "amount": "5kg", "price": 4200, "unit": "箱"},
        {"kind": peach,  "grade": "優", "size": "M", "amount": "5kg", "price": 3600, "unit": "箱"},
        {"kind":plum,  "grade": "秀", "size": "LL", "amount": "5kg", "price": 5000, "unit": "箱"},
        {"kind":plum,  "grade": "秀", "size": "L", "amount": "5kg", "price": 5000, "unit": "箱"},
        {"kind":plum,  "grade": "秀", "size": "M", "amount": "5kg", "price": 4400, "unit": "箱"},
        {"kind":plum,  "grade": "優", "size": "LL", "amount": "5kg", "price": 4200, "unit": "箱"},
        {"kind":plum,  "grade": "優", "size": "L", "amount": "5kg", "price": 4200, "unit": "箱"},
        {"kind":plum,  "grade": "優", "size": "M", "amount": "5kg", "price": 3600, "unit": "箱"},
        
    ]

    for row in pricetable:
        PriceTable.objects.get_or_create(
            kind=row["kind"],
            grade=row["grade"],
            size=row["size"],
            amount=row["amount"],
            price=row["price"],
            unit=row["unit"],
        )
    
    # Create delivery dates for each product
    from datetime import date, timedelta

    # Set start_dates
    products_with_start_dates = {
        "あかつき": date(2025, 7, 25),
        "なつっこ": date(2025, 8, 3),
        "大石早生": date(2025, 7, 5),
        "ソルダム": date(2025, 7, 20),
    }

    for product_name, start_date in products_with_start_dates.items():
        try:
            product = ProductName.objects.get(name=product_name)
            for i in range(7): #Add 7 days
                ProductDeliveryDate.objects.get_or_create(
                    product=product,
                    date=start_date + timedelta(days=i)
                )
            print(f"Created delivery dates for {product_name}")
        except ProductName.DoesNotExist:
            print(f"Product {product_name} not found.Please check spelling.")

if __name__ == "__main__":
    run()