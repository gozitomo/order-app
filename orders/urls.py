from django.urls import path
from . import views

urlpatterns = [
    path('mypage/', views.order_history, name='order_history'),
]