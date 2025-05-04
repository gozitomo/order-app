from django.db import models
from django.contrib.auth.models import User
from products.models import FruitKind, ProductName, PriceTable, ProductDeliveryDate
from datetime import date
from django.utils.timezone import now

# Create your models here.
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='未処理')
    total_quantity = models.PositiveIntegerField(default=0)
    total_price = models.PositiveIntegerField(default=0)
    final_total = models.PositiveIntegerField(default=0)
    total_tax = models.PositiveIntegerField(default=0)
    total_shipping_fee = models.PositiveIntegerField(default=0)
    shipping_tax = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"注文ID:{self.id} - {self.user.username}"

class Invoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    invoice_type = models.CharField(max_length=10)
    invoice_id = models.CharField(max_length=20, unique=True)
    issued_date = models.DateField(auto_now_add=True)
    period_start = models.DateField()
    period_end = models.DateField()
    total_extax = models.DecimalField(max_digits=10, decimal_places=0)
    tax8 = models.DecimalField(max_digits=10, decimal_places=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=0)
    shipping_extax = models.DecimalField(max_digits=10, decimal_places=0)
    tax10 = models.DecimalField(max_digits=10, decimal_places=0)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=0)
    final_extax = models.DecimalField(max_digits=10, decimal_places=0)
    final_tax = models.DecimalField(max_digits=10, decimal_places=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=0)
    
    def generate_invoice_number():
        today = now().date()
        yyyymm = today.strftime("%Y%m")
        last_invoice = Invoice.objects.filter(invoice_id__startswith=yyyymm).order_by('-invoice_id').first()
        if last_invoice:
            last_seq = int(last_invoice.invoice_id[-3:])
            return f"{yyyymm}-{last_seq + 1:03d}"
        else:
            return f"{yyyymm}-001"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(ProductName, on_delete=models.CASCADE)
    grade = models.CharField(max_length=20, default="")
    size = models.CharField(max_length=20, default="")
    amount = models.CharField(max_length=20, default="")
    unit = models.CharField(max_length=20, default="")
    price = models.PositiveIntegerField(default=0)
    quantity = models.PositiveIntegerField()
    subtotal = models.PositiveIntegerField(default=0)
    tax = models.PositiveIntegerField(default=0)
    shipping_fee = models.PositiveIntegerField(default=0)
    shipping_tax = models.PositiveIntegerField(default=0)
    delivery_date = models.DateField(default=date.today())
    delivery_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    invoice_id = models.ForeignKey(Invoice, null=True, blank=True, on_delete=models.SET_NULL, related_name='items')
    tracking_id = models.CharField(max_length=20, null=True)

    def __str__(self):
        return f"{self.product.name} ({self.grade}/{self.size}/{self.amount})×{self.quantity}"

    def generate_delivery_number():
        today = now().date()
        yyyymmdd = OrderItem.objects.filter(delivery_number__startwith=yyyymmdd).order_by('-delivery_number').first()
        if last_item and last_item.delivery_number:
            last_seq = int(last_item.delivery_number[-3:])
            return f"{yyyymmdd}-{last_seq+1:03d}"
        else:
            return f"{yyyymmdd}-001"

    def get_total_price(self):
        return self.product.price * self.quautity

class ShippingFeeRule(models.Model):
    min_qty = models.PositiveIntegerField()
    max_qty = models.PositiveIntegerField()
    fee = models.PositiveIntegerField()
    tax = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.min_qty}～{self.max_qty}kg：{self.fee}円"

