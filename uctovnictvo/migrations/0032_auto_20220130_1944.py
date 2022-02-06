# Generated by Django 3.2.6 on 2022-01-30 19:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0031_auto_20220130_1826'),
    ]

    operations = [
        migrations.AddField(
            model_name='dohoda',
            name='dohoda_odoslana',
            field=models.DateField(blank=True, help_text='Dátum odovzdania dohody na sekretariát na odoslanie na podpis (poštou). Vytvorí sa záznam v <a href="/admin/dennik/dokument/">denníku prijatej a odoslanej pošty</a>.', null=True, verbose_name='Autorovi na podpis '),
        ),
        migrations.AddField(
            model_name='historicaldobps',
            name='dohoda_odoslana',
            field=models.DateField(blank=True, help_text='Dátum odovzdania dohody na sekretariát na odoslanie na podpis (poštou). Vytvorí sa záznam v <a href="/admin/dennik/dokument/">denníku prijatej a odoslanej pošty</a>.', null=True, verbose_name='Autorovi na podpis '),
        ),
        migrations.AddField(
            model_name='historicaldopc',
            name='dohoda_odoslana',
            field=models.DateField(blank=True, help_text='Dátum odovzdania dohody na sekretariát na odoslanie na podpis (poštou). Vytvorí sa záznam v <a href="/admin/dennik/dokument/">denníku prijatej a odoslanej pošty</a>.', null=True, verbose_name='Autorovi na podpis '),
        ),
        migrations.AddField(
            model_name='historicaldovp',
            name='dohoda_odoslana',
            field=models.DateField(blank=True, help_text='Dátum odovzdania dohody na sekretariát na odoslanie na podpis (poštou). Vytvorí sa záznam v <a href="/admin/dennik/dokument/">denníku prijatej a odoslanej pošty</a>.', null=True, verbose_name='Autorovi na podpis '),
        ),
    ]