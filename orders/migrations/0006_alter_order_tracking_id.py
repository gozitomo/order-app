# Generated by Django 5.2 on 2025-06-07 12:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_order_custom_deli_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='tracking_id',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
