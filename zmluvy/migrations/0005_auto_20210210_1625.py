# Generated by Django 3.1.6 on 2021-02-10 15:25

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('zmluvy', '0004_zmluva_datum_pridania'),
    ]

    operations = [
        migrations.AddField(
            model_name='osoba',
            name='datum_aktualizacie',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Dátum aktualizácie'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='zmluva',
            name='datum_aktualizacie',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Dátum aktualizácie'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='osoba',
            name='posobisko',
            field=models.CharField(blank=True, max_length=200, verbose_name='Pôsobisko'),
        ),
        migrations.AlterField(
            model_name='osoba',
            name='titul_pred_menom',
            field=models.CharField(blank=True, max_length=100, verbose_name='Titul pred menom'),
        ),
        migrations.AlterField(
            model_name='osoba',
            name='titul_za_menom',
            field=models.CharField(blank=True, max_length=100, verbose_name='Titul za menom'),
        ),
    ]