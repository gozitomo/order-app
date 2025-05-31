from django.contrib import admin
from .models import FruitKind, ProductName, PriceTable, ProductDeliveryDate

# Register your models here.

@admin.register(FruitKind)
class FruitKindAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

admin.site.register(ProductName)
admin.site.register(PriceTable)
admin.site.register(ProductDeliveryDate)
