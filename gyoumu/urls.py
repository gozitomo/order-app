from django.urls import path
from . import views

urlpatterns = [
    path('menu/',views.gyoumu_menu, name='gyoumu_menu'),
    path('menu/csv_uploader/',views.upload_generic_csv, name='csv_upload'),
    path('menu/download/',views.export_model_csv, name='export_model_csv'),
    path('invoice/monthly/generate/',views.monthly_invoice_pdf, name='generate_monthly_invoice'),
    path('menu/order_confirm/',views.order_confirm, name='order_confirm'),
    path('menu/order_confirm/<int:order_id>',views.order_confirm, name='order_confirm'),
    path('menu/order_confirm/ship_comp/<int:order_id>',views.ship_comp, name='ship_comp'),
]