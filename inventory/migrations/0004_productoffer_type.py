# Generated by Django 4.2.2 on 2023-06-30 17:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_remove_productoffer_offer_typef'),
    ]

    operations = [
        migrations.AddField(
            model_name='productoffer',
            name='type',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='offer_type_products', to='inventory.offertype'),
            preserve_default=False,
        ),
    ]
