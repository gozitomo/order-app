from django.db import models
from users.models import UserGroup

# Create your models here.
class FruitKind(models.Model):
    """ kind of fruit, like Peach, Plum, Chestnut, etc"""
    STATUS_CHOICES = [
        ('available', '受付中'),
        ('closed', '準備中'),
    ]
    name = models.CharField(max_length=50)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='available')

    def __str__(self):
        return self.name

class ProductName(models.Model):
    """ Product name like あかつき, なつっこ, etc. """
    name = models.CharField(max_length=50)
    kind = models.ForeignKey(FruitKind, on_delete=models.CASCADE, related_name="products")
    description = models.TextField(blank=True)
    season = models.CharField(max_length=50)
    sort_no = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} ({self.kind.name})"

class PriceTable(models.Model):
    STATUS_CHOICES = [
        ('available', '受付中'),
        ('closed', '準備中'),
    ]
    kind = models.ForeignKey(FruitKind, on_delete=models.CASCADE, related_name="options")
    grade = models.CharField(max_length=20)
    size = models.CharField(max_length=20)
    unit = models.CharField(max_length=20, default='4.3kg/箱')
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.PositiveIntegerField()
    tax10_flg = models.BooleanField(default=True)
    user_group = models.ForeignKey(UserGroup, default=1, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='available')

    def __str__(self):
        return f"{self.kind.name} {self.grade} {self.size}"
    

class ProductDeliveryDate(models.Model):
    product = models.ForeignKey(ProductName, on_delete=models.CASCADE, related_name='available_dates')
    date = models.DateField()

    def __str__(self):
        return f"{self.product.name} - {self.date}"