# Generated by Django 3.2.4 on 2023-12-14 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0143_auto_20231211_1547'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalnepritomnost',
            name='poznamka',
            field=models.CharField(blank=True, max_length=60, null=True, verbose_name='Poznámka'),
        ),
        migrations.AddField(
            model_name='nepritomnost',
            name='poznamka',
            field=models.CharField(blank=True, max_length=60, null=True, verbose_name='Poznámka'),
        ),
    ]
