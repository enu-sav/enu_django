# Generated by Django 3.2.6 on 2022-01-20 13:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0023_auto_20211217_1518'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalprijatafaktura',
            name='doslo_datum',
            field=models.DateField(null=True, verbose_name='Došlo dňa'),
        ),
        migrations.AlterField(
            model_name='historicalprijatafaktura',
            name='splatnost_datum',
            field=models.DateField(null=True, verbose_name='Dátum splatnosti'),
        ),
        migrations.AlterField(
            model_name='prijatafaktura',
            name='doslo_datum',
            field=models.DateField(null=True, verbose_name='Došlo dňa'),
        ),
        migrations.AlterField(
            model_name='prijatafaktura',
            name='splatnost_datum',
            field=models.DateField(null=True, verbose_name='Dátum splatnosti'),
        ),
    ]
