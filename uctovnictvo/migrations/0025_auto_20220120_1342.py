# Generated by Django 3.2.6 on 2022-01-20 13:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0024_auto_20220120_1340'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalprijatafaktura',
            name='suma',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Zadajte príjmy ako kladné, výdavky ako záporné číslo', max_digits=8, verbose_name='Suma'),
        ),
        migrations.AlterField(
            model_name='prijatafaktura',
            name='suma',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Zadajte príjmy ako kladné, výdavky ako záporné číslo', max_digits=8, verbose_name='Suma'),
        ),
    ]