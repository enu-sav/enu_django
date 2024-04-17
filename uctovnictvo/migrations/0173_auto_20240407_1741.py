# Generated by Django 3.2.4 on 2024-04-07 17:41

from django.db import migrations, models
import uctovnictvo.models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0172_auto_20240407_1141'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalnepritomnost',
            name='subor_nepritomnost',
            field=models.TextField(blank=True, help_text="XLSX súbor so zoznamom neprítomností z Biometric-u (<strong>Reporty a exporty</strong> > <strong>Evidencia dochádzky</strong> > <strong>Spustit report</strong> a uložiť ako Excel).<br />Po vložení treba akciou 'Generovať záznamy neprítomnosti' vytvoriť jednotlivé záznamy.<br />Ak sa údaje v Biometric-u zmenia, súbor opakovane exportujte a vložte.", max_length=100, null=True, verbose_name='Import. súbor'),
        ),
        migrations.AlterField(
            model_name='nepritomnost',
            name='subor_nepritomnost',
            field=models.FileField(blank=True, help_text="XLSX súbor so zoznamom neprítomností z Biometric-u (<strong>Reporty a exporty</strong> > <strong>Evidencia dochádzky</strong> > <strong>Spustit report</strong> a uložiť ako Excel).<br />Po vložení treba akciou 'Generovať záznamy neprítomnosti' vytvoriť jednotlivé záznamy.<br />Ak sa údaje v Biometric-u zmenia, súbor opakovane exportujte a vložte.", null=True, upload_to=uctovnictvo.models.nepritomnost_upload_location, verbose_name='Import. súbor'),
        ),
    ]