# Generated by Django 3.2.6 on 2022-03-24 17:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0042_auto_20220320_0920'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='historicalprijatafaktura',
            options={'get_latest_by': 'history_date', 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical Prijatá faktúra'},
        ),
        migrations.AlterModelOptions(
            name='prijatafaktura',
            options={'verbose_name': 'Prijatá faktúra', 'verbose_name_plural': 'Faktúry - Prijaté faktúry'},
        ),
        migrations.AlterField(
            model_name='historicalprijatafaktura',
            name='cislo',
            field=models.CharField(max_length=50, verbose_name='Číslo'),
        ),
        migrations.AlterField(
            model_name='historicalprijatafaktura',
            name='dane_na_uhradu',
            field=models.DateField(blank=True, help_text='Zadajte dátum odovzdania podpísaného platobného príkazu a krycieho listu na sekretariát na odoslanie THS. <br />Vytvorí sa záznam v <a href="/admin/dennik/dokument/">denníku prijatej a odoslanej pošty</a>.', null=True, verbose_name='Dané na úhradu dňa'),
        ),
        migrations.AlterField(
            model_name='historicalprijatafaktura',
            name='predmet',
            field=models.CharField(max_length=100, verbose_name='Predmet'),
        ),
        migrations.AlterField(
            model_name='historicalprijatafaktura',
            name='suma',
            field=models.DecimalField(decimal_places=2, max_digits=8, null=True, verbose_name='Suma'),
        ),
        migrations.AlterField(
            model_name='prijatafaktura',
            name='cislo',
            field=models.CharField(max_length=50, verbose_name='Číslo'),
        ),
        migrations.AlterField(
            model_name='prijatafaktura',
            name='dane_na_uhradu',
            field=models.DateField(blank=True, help_text='Zadajte dátum odovzdania podpísaného platobného príkazu a krycieho listu na sekretariát na odoslanie THS. <br />Vytvorí sa záznam v <a href="/admin/dennik/dokument/">denníku prijatej a odoslanej pošty</a>.', null=True, verbose_name='Dané na úhradu dňa'),
        ),
        migrations.AlterField(
            model_name='prijatafaktura',
            name='predmet',
            field=models.CharField(max_length=100, verbose_name='Predmet'),
        ),
        migrations.AlterField(
            model_name='prijatafaktura',
            name='suma',
            field=models.DecimalField(decimal_places=2, max_digits=8, null=True, verbose_name='Suma'),
        ),
    ]
