# Generated by Django 3.2.4 on 2023-10-09 09:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0127_auto_20230717_2141'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalnepritomnost',
            name='nepritomnost_typ',
            field=models.CharField(blank=True, choices=[('materská', 'Materská'), ('ocr', 'OČR'), ('pn', 'PN'), ('dovolenka', 'Dovolenka'), ('dovolenka2', 'Poldeň dovolenky'), ('lekar', 'Návšteva u lekára (L)'), ('lekardoprovod', 'Doprovod k lekárovi (L/D)'), ('pzv', 'Pracovné voľno (PzV, PV, P, S, KZVS, POH)'), ('neplatene', 'Neplatené voľno'), ('sluzobna', 'Služobná cesta'), ('pracadoma', 'Práca na doma'), ('skolenie', 'Školenie')], max_length=20, null=True, verbose_name='Typ neprítomnosti'),
        ),
        migrations.AlterField(
            model_name='nepritomnost',
            name='nepritomnost_typ',
            field=models.CharField(blank=True, choices=[('materská', 'Materská'), ('ocr', 'OČR'), ('pn', 'PN'), ('dovolenka', 'Dovolenka'), ('dovolenka2', 'Poldeň dovolenky'), ('lekar', 'Návšteva u lekára (L)'), ('lekardoprovod', 'Doprovod k lekárovi (L/D)'), ('pzv', 'Pracovné voľno (PzV, PV, P, S, KZVS, POH)'), ('neplatene', 'Neplatené voľno'), ('sluzobna', 'Služobná cesta'), ('pracadoma', 'Práca na doma'), ('skolenie', 'Školenie')], max_length=20, null=True, verbose_name='Typ neprítomnosti'),
        ),
    ]
