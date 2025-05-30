# Generated by Django 5.2 on 2025-05-31 10:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('subtotal', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='ShippingFeeRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_weight', models.PositiveIntegerField()),
                ('max_weight', models.PositiveIntegerField()),
                ('cool_flg', models.BooleanField(default=False)),
                ('shipping_fee', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ShippingRegion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='DeliNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deli_note_id', models.CharField(max_length=20, unique=True)),
                ('deli_date', models.DateField(auto_now_add=True)),
                ('tax8_price', models.DecimalField(decimal_places=0, max_digits=10)),
                ('tax10_price', models.DecimalField(decimal_places=0, max_digits=10)),
                ('final_price', models.DecimalField(decimal_places=0, max_digits=10)),
                ('tax8_extax', models.DecimalField(decimal_places=0, max_digits=10)),
                ('tax10_extax', models.DecimalField(decimal_places=0, max_digits=10)),
                ('final_extax', models.DecimalField(decimal_places=0, max_digits=10)),
                ('tax8', models.DecimalField(decimal_places=0, max_digits=10)),
                ('tax10', models.DecimalField(decimal_places=0, max_digits=10)),
                ('final_tax', models.DecimalField(decimal_places=0, max_digits=10)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_type', models.CharField(max_length=10)),
                ('invoice_id', models.CharField(max_length=20, unique=True)),
                ('issued_date', models.DateField(auto_now_add=True)),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('tax8_price', models.DecimalField(decimal_places=0, max_digits=10)),
                ('tax10_price', models.DecimalField(decimal_places=0, max_digits=10)),
                ('final_price', models.DecimalField(decimal_places=0, max_digits=10)),
                ('tax8_extax', models.DecimalField(decimal_places=0, max_digits=10)),
                ('tax10_extax', models.DecimalField(decimal_places=0, max_digits=10)),
                ('final_extax', models.DecimalField(decimal_places=0, max_digits=10)),
                ('tax8', models.DecimalField(decimal_places=0, max_digits=10)),
                ('tax10', models.DecimalField(decimal_places=0, max_digits=10)),
                ('final_tax', models.DecimalField(decimal_places=0, max_digits=10)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('order_id', models.CharField(max_length=6, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tracking_id', models.CharField(max_length=20, null=True)),
                ('cool_flg', models.BooleanField(default=False)),
                ('status', models.CharField(choices=[('tentative', '仮注文'), ('received', '確認済み'), ('preparing', '準備中'), ('shipped', '発送済'), ('canceled', 'キャンセル済')], default='tentative', max_length=50)),
                ('tax8_price', models.PositiveIntegerField(default=0)),
                ('tax8', models.PositiveIntegerField(default=0)),
                ('tax10_price', models.PositiveIntegerField(default=0)),
                ('tax10', models.PositiveIntegerField(default=0)),
                ('total_weight', models.PositiveIntegerField(default=0)),
                ('shipping_price', models.PositiveIntegerField(default=0)),
                ('shipping_tax', models.PositiveIntegerField(default=0)),
                ('final_price', models.PositiveIntegerField(default=0)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('deli_note_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='items', to='orders.delinote')),
                ('invoice_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='items', to='orders.invoice')),
            ],
        ),
    ]
