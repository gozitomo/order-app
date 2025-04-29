from django.contrib import admin
from .models import FruitKind, ProductName, PriceTable, ProductDeliveryDate

# Register your models here.
admin.site.register(FruitKind)
admin.site.register(ProductName)
admin.site.register(PriceTable)
admin.site.register(ProductDeliveryDate)
