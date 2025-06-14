from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('orders/history/', views.order_history, name='order_history'),
    path('orders/', views.order_top, name='order_top'),
    path('orders/new/<int:product_id>/', views.neworder, name='new_order'),
    path('orders/detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/change/<int:order_id>/', views.order_change, name='order_change'),
    path('orders/cancel/<int:order_id>/', views.order_cancel, name='order_cancel'),
    path('orders/order_confirm/',views.order_confirm, name='order_confirm'),
    path('orders/order_confirm/<int:order_id>',views.order_confirm, name='order_confirm'),
    path('orders/order_confirm/ship_comp/<int:order_id>',views.ship_comp, name='ship_comp'),
    path('orders/<int:order_id>/invoice/pdf/',views.order_invoice_pdf, name='order_invoice_pdf'),
    path('invoice/<int:invoice_id>/pdf/',views.invoice_pdf, name='invoice_pdf'),
    path('orders/my_invoice_list',views.my_invoices, name='my_invoices'),
]