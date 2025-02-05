# Generated by Django 3.2.4 on 2024-12-12 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0209_auto_20241031_1656'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalnepritomnost',
            name='nepritomnost_typ',
            field=models.CharField(blank=True, choices=[('materská', 'MD/RD'), ('ocr', 'OČR'), ('pn', 'PN'), ('dovolenka', 'Dovolenka'), ('dovolenka2', 'Poldeň dovolenky'), ('lekar', 'Návšteva u lekára (L)'), ('lekardoprovod', 'Doprovod k lekárovi (L/D)'), ('pzv', 'Platené zdr. voľno podľa KZ'), ('pv', 'Pracovné voľno (PV, P, S, KZVS, POH)'), ('neplatene', 'Neplatené voľno'), ('sluzobna', 'Služobná cesta'), ('riaditelskevolno', 'Riaditelské voľno'), ('pracadoma', 'Práca na doma'), ('skolenie', 'Školenie'), ('zrusena', 'Zrušená')], help_text="Ak sa tento záznam nedostal do Softipu a je to chyba, zvoľte 'Zrušená' v poli poznámka uveďte dôvod.", max_length=20, null=True, verbose_name='Typ neprítomnosti'),
        ),
        migrations.AlterField(
            model_name='nepritomnost',
            name='nepritomnost_typ',
            field=models.CharField(blank=True, choices=[('materská', 'MD/RD'), ('ocr', 'OČR'), ('pn', 'PN'), ('dovolenka', 'Dovolenka'), ('dovolenka2', 'Poldeň dovolenky'), ('lekar', 'Návšteva u lekára (L)'), ('lekardoprovod', 'Doprovod k lekárovi (L/D)'), ('pzv', 'Platené zdr. voľno podľa KZ'), ('pv', 'Pracovné voľno (PV, P, S, KZVS, POH)'), ('neplatene', 'Neplatené voľno'), ('sluzobna', 'Služobná cesta'), ('riaditelskevolno', 'Riaditelské voľno'), ('pracadoma', 'Práca na doma'), ('skolenie', 'Školenie'), ('zrusena', 'Zrušená')], help_text="Ak sa tento záznam nedostal do Softipu a je to chyba, zvoľte 'Zrušená' v poli poznámka uveďte dôvod.", max_length=20, null=True, verbose_name='Typ neprítomnosti'),
        ),
    ]
