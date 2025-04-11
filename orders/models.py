from django.db import models
from django.contrib.auth.models import User
from products.models import Product

# Create your models here.
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='未処理')
    total_quantity = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    final_total = models.PositiveIntegerField(default=0)
    final_tax = models.PositiveIntegerField(default=0)
    shipping_fee = models.PositiveIntegerField(default=0)
    shipping_tax = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"注文ID:{self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    subtotal = models.PositiveIntegerField(default=0)
    tax = models.PositiveIntegerField(default=0)

    def get_total_price(self):
        return self.product.price * self.quautity

class ShippingFeeRule(models.Model):
    min_qty = models.PositiveIntegerField()
    max_qty = models.PositiveIntegerField()
    fee = models.PositiveIntegerField()
    tax = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.min_qty}～{self.max_qty}kg：{self.fee}円"
