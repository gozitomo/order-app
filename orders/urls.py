from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.top_page, name='top_page'),
    path('signup/', views.signup, name='signup'),
    path('orders/history/', views.order_history, name='order_history'),
    path('orders/', views.order_top, name='order_top'),
    path('orders/new/<int:product_id>/', views.neworder, name='new_order'),
    path('orders/detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/change/<int:order_id>/', views.order_change, name='order_change'),
    path('orders/cancel/<int:order_id>/', views.order_cancel, name='order_cancel'),
    path('orders/<int:order_id>/invoice/pdf/',views.order_invoice_pdf, name='order_invoice_pdf'),
    path('menu/',views.gyoumu_menu, name='gyoumu_menu'),
    path('menu/upload_pricetable',views.upload_pricetable, name='upload_pricetable'),
    path('invoice/monthly/generate/',views.monthly_invoice_pdf, name='generate_monthly_invoice'),
    path('invoice/<int:invoice_id>/pdf/',views.invoice_pdf, name='invoice_pdf'),
    path('orders/my_invoice_list',views.my_invoices, name='my_invoices'),
]