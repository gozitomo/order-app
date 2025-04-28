from django.db import models

# Create your models here.
class FruitKind(models.Model):
    """ kind of fruit, like Peach, Plum, Chestnut, etc"""
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class ProductName(models.Model):
    """ Product name like あかつき, なつっこ, etc. """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    kind = models.ForeignKey(FruitKind, on_delete=models.CASCADE, related_name="products")
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.kind.name})"

class PriceTable(models.Model):
    kind = models.ForeignKey(FruitKind, on_delete=models.CASCADE, related_name="options")
    grade = models.CharField(max_length=20)
    size = models.CharField(max_length=20)
    amount = models.CharField(max_length=20)
    unit = models.CharField(max_length=20, default='箱')
    price = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.kind.name} {self.grade} {self.size}"

class ProductDeliveryDate(models.Model):
    product = models.ForeignKey(ProductName, on_delete=models.CASCADE, related_name='available_dates')
    date = models.DateField()

    def __str__(self):
        return f"{self.product.name} - {self.date}"