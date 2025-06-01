from django.contrib import admin
from .models import FruitKind, ProductName, PriceTable, ProductDeliveryDate

# Register your models here.

@admin.register(FruitKind)
class FruitKindAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

@admin.register(PriceTable)
class PriceTableAdmin(admin.ModelAdmin):
    list_display = ('kind', 'grade', 'size', 'unit', 'user_group')
    list_filter = ('user_group', 'kind')

admin.site.register(ProductName)
admin.site.register(ProductDeliveryDate)
