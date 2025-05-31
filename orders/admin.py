from django.contrib import admin
from .models import Order, OrderItem, ShippingFeeRule, Invoice, ShippingRegion

# Register your models here.

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'created_at', 'status')
    inlines = [OrderItemInline]

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(ShippingRegion)
admin.site.register(ShippingFeeRule)
admin.site.register(Invoice)
