# Generated by Django 3.2.6 on 2022-12-01 16:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0103_auto_20221201_1555'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalprijatafaktura',
            name='sumacm',
            field=models.DecimalField(decimal_places=2, help_text="V prípade uvedenia sumy v cudzej mene vložte do poľa 'Suma' nulu. Pole 'Suma vypňte až bude známa uhradená suma v EUR", max_digits=8, null=True, verbose_name='Suma cudzej mene'),
        ),
        migrations.AddField(
            model_name='prijatafaktura',
            name='sumacm',
            field=models.DecimalField(decimal_places=2, help_text="V prípade uvedenia sumy v cudzej mene vložte do poľa 'Suma' nulu. Pole 'Suma vypňte až bude známa uhradená suma v EUR", max_digits=8, null=True, verbose_name='Suma cudzej mene'),
        ),
    ]
