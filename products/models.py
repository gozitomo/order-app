from django.db import models

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=50, default='kg')

    def __str__(self):
        return self.name

