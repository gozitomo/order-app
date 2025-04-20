from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.top_page, name='top_page'),
    path('signup/', views.signup, name='signup'),
    path('mypage/', views.order_history, name='order_history'),
    path('orders/', views.place_order, name='place_order'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('orders/<int:order_id>/invoice/pdf/',views.order_invoice_pdf, name='order_invoice_pdf'),
    path('menu/',views.gyoumu_menu, name='gyoumu_menu'),
    path('invoice/monthly/generate/',views.monthly_invoice_pdf, name='generate_monthly_invoice'),
    path('invoice/<int:invoice_id>/pdf/',views.invoice_pdf, name='invoice_pdf'),
    path('mypage/my_invoice_list',views.my_invoices, name='my_invoices'),
]