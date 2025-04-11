# Generated by Django 5.2 on 2025-04-11 02:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShippingFeeRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_qty', models.PositiveIntegerField()),
                ('max_qty', models.PositiveIntegerField()),
                ('fee', models.PositiveIntegerField()),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='total',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='order',
            name='total_quantity',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='subtotal',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
