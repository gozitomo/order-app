from django.db import models
from django.contrib.auth.models import User
from products.models import FruitKind, ProductName, PriceTable, ProductDeliveryDate
from datetime import date
from django.utils.timezone import now

# Create your models here.


def generate_order_id():
    this_year = now().year % 100
    prefix = f"{this_year:02d}"

    last_order = Order.objects.filter(order_id__startswith=prefix).order_by('-order_id').first()
    if last_order:
        last_number = int(last_order.order_id[-4:])
        new_number = last_number + 1
    else:
        new_number = 1
    return f"{prefix}{new_number:04d}"

def generate_delinote_id():
    this_year = now().year % 100
    prefix = f"{this_year:02d}"
    last_order = Order.objects.filter()

    last_order = Order.objects.filter(order_id__startswith=prefix).order_by('-order_id').first()
    if last_order:
        last_number = int(last_order.order_id[-4:])
        new_number = last_number + 1
    else:
        new_number = 1
    return f"{prefix}{new_number:04d}"

class Invoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    invoice_type = models.CharField(max_length=10)
    invoice_id = models.CharField(max_length=20, unique=True)
    issued_date = models.DateField(auto_now_add=True)
    period_start = models.DateField()
    period_end = models.DateField()
    tax8_price = models.DecimalField(max_digits=10, decimal_places=0)
    tax10_price = models.DecimalField(max_digits=10, decimal_places=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=0)
    tax8_extax = models.DecimalField(max_digits=10, decimal_places=0)
    tax10_extax = models.DecimalField(max_digits=10, decimal_places=0)
    final_extax = models.DecimalField(max_digits=10, decimal_places=0)
    tax8 = models.DecimalField(max_digits=10, decimal_places=0)
    tax10 = models.DecimalField(max_digits=10, decimal_places=0)
    final_tax = models.DecimalField(max_digits=10, decimal_places=0)
    
    def generate_invoice_number():
        today = now().date()
        yyyymm = today.strftime("%Y%m")
        last_invoice = Invoice.objects.filter(invoice_id__startswith=yyyymm).order_by('-invoice_id').first()
        if last_invoice:
            last_seq = int(last_invoice.invoice_id[-3:])
            return f"{yyyymm}-{last_seq + 1:03d}"
        else:
            return f"{yyyymm}-001"


class DeliNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    deli_note_id = models.CharField(max_length=20, unique=True)
    deli_date = models.DateField(auto_now_add=True)
    tax8_price = models.DecimalField(max_digits=10, decimal_places=0)
    tax10_price = models.DecimalField(max_digits=10, decimal_places=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=0)
    tax8_extax = models.DecimalField(max_digits=10, decimal_places=0)
    tax10_extax = models.DecimalField(max_digits=10, decimal_places=0)
    final_extax = models.DecimalField(max_digits=10, decimal_places=0)
    tax8 = models.DecimalField(max_digits=10, decimal_places=0)
    tax10 = models.DecimalField(max_digits=10, decimal_places=0)
    final_tax = models.DecimalField(max_digits=10, decimal_places=0)
    
    def generate_deli_note_id():
        today = now().date()
        yyyymm = today.strftime("%Y%m")
        last_deli_note = DeliNote.objects.filter(deli_note_id__startswith=yyyymm).order_by('-deli_note_id').first()
        if last_deli_note:
            last_seq = int(last_deli_note.invoice_id[-3:])
            return f"{yyyymm}-{last_seq + 1:03d}"
        else:
            return f"{yyyymm}-001"

class Order(models.Model):
    def get_default_product_delivery_date():
        return ProductDeliveryDate.objects.first().id

    STATUS_CHOICES = [
        ('tentative', '仮注文'),
        ('received', '受注'),
        ('preparing', '準備中'), #キャンセル不可
        ('shipped', '発送済'), #キャンセル不可
        ('canceled', '取消済'),
    ]
    order_id = models.CharField(primary_key=True, max_length=6)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    product_delivery_date = models.ForeignKey(ProductDeliveryDate, on_delete=models.CASCADE, null=True)
    custom_deli_date = models.DateField(blank=True, null=True)
    tracking_id = models.CharField(max_length=20, null=True, blank=True)
    cool_flg = models.BooleanField(default=False)
    pickup_flg = models.BooleanField(default=False)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='tentative')
    tax8_price = models.PositiveIntegerField(default=0)
    tax8 = models.PositiveIntegerField(default=0)
    tax10_price = models.PositiveIntegerField(default=0)
    tax10 = models.PositiveIntegerField(default=0)
    total_weight = models.PositiveIntegerField(default=0)
    shipping_price = models.PositiveIntegerField(default=0)
    shipping_tax = models.PositiveIntegerField(default=0)
    final_price = models.PositiveIntegerField(default=0)
    remarks = models.TextField(blank=True, null=True)
    invoice_id = models.ForeignKey(Invoice, null=True, blank=True, on_delete=models.SET_NULL, related_name='items')
    deli_note_id = models.ForeignKey(DeliNote, null=True, blank=True, on_delete=models.SET_NULL, related_name='items')

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = generate_order_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"注文番号:{self.order_id} - {self.user.username}"
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    price_table = models.ForeignKey(PriceTable, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductName, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    subtotal = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} ({self.price_table.grade}/{self.price_table.size}/{self.price_table.unit})×{self.quantity}"

    # def generate_delivery_number():
    #     today = now().date()
    #     yyyymmdd = OrderItem.objects.filter(delivery_number__startwith=yyyymmdd).order_by('-delivery_number').first()
    #     if last_item and last_item.delivery_number:
    #         last_seq = int(last_item.delivery_number[-3:])
    #         return f"{yyyymmdd}-{last_seq+1:03d}"
    #     else:
    #         return f"{yyyymmdd}-001"

    def get_total_price(self):
        return self.price_table.price * self.quautity


class ShippingRegion(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.name}"


class ShippingFeeRule(models.Model):
    region = models.ForeignKey(ShippingRegion, related_name='shipping_fee_rules', on_delete=models.CASCADE, null=True)
    min_weight = models.PositiveIntegerField()
    max_weight = models.PositiveIntegerField()
    cool_flg = models.BooleanField(default=False)
    shipping_fee = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.region}:{self.min_weight}～{self.max_weight}kg：{self.shipping_fee}円 {self.cool_flg}"
