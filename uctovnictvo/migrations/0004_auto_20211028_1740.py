# Generated by Django 3.2.6 on 2021-10-28 17:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0003_zamestnanecdohodar_polymorphic_ctype'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicalplatovyvymer',
            name='polymorphic_ctype',
        ),
        migrations.RemoveField(
            model_name='platovyvymer',
            name='polymorphic_ctype',
        ),
    ]
