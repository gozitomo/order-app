from django.urls import path
from . import views

urlpatterns = [
    path('menu/',views.gyoumu_menu, name='gyoumu_menu'),
    path('menu/csv_uploader/',views.upload_generic_csv, name='csv_upload'),
    path('invoice/monthly/generate/',views.monthly_invoice_pdf, name='generate_monthly_invoice'),
]