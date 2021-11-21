# Generated by Django 3.2.6 on 2021-11-16 18:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zmluvy', '0009_auto_20211114_1139'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalplatbaautorskasumar',
            name='kryci_list_odoslany',
            field=models.DateField(blank=True, help_text='Dátum odoslania hárku <em>Krycí list</en> účtovníčke (internou poštou)</em>', null=True, verbose_name="'Krycí list' odoslaný"),
        ),
        migrations.AlterField(
            model_name='historicalplatbaautorskasumar',
            name='na_vyplatenie_odoslane',
            field=models.DateField(blank=True, help_text='Dátum odoslania hárku <em>Na vyplatenie</en> účtovníčke (mailom)</em>', null=True, verbose_name="'Na vyplatenie' odoslané"),
        ),
        migrations.AlterField(
            model_name='historicalplatbaautorskasumar',
            name='obdobie',
            field=models.CharField(default='2021-11-16', help_text='Ako identifikátor vyplácania sa použije dátum jeho vytvorenia', max_length=20, verbose_name='Identifikátor vyplácania'),
        ),
        migrations.AlterField(
            model_name='platbaautorskasumar',
            name='kryci_list_odoslany',
            field=models.DateField(blank=True, help_text='Dátum odoslania hárku <em>Krycí list</en> účtovníčke (internou poštou)</em>', null=True, verbose_name="'Krycí list' odoslaný"),
        ),
        migrations.AlterField(
            model_name='platbaautorskasumar',
            name='na_vyplatenie_odoslane',
            field=models.DateField(blank=True, help_text='Dátum odoslania hárku <em>Na vyplatenie</en> účtovníčke (mailom)</em>', null=True, verbose_name="'Na vyplatenie' odoslané"),
        ),
        migrations.AlterField(
            model_name='platbaautorskasumar',
            name='obdobie',
            field=models.CharField(default='2021-11-16', help_text='Ako identifikátor vyplácania sa použije dátum jeho vytvorenia', max_length=20, verbose_name='Identifikátor vyplácania'),
        ),
    ]