# Generated by Django 4.2.2 on 2023-07-03 01:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_category_font_awesome_category_icon_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='font_awesome',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]