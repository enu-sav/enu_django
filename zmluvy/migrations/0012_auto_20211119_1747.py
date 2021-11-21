# Generated by Django 3.2.6 on 2021-11-19 17:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zmluvy', '0011_auto_20211118_0945'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalzmluvaautor',
            name='zmluva_odoslana',
            field=models.DateField(blank=True, help_text='Dátum odoslania zmluvy na podpis (poštou)', null=True, verbose_name='Odoslaná na podpis '),
        ),
        migrations.AddField(
            model_name='historicalzmluvaautor',
            name='zmluva_vratena',
            field=models.DateField(blank=True, help_text='Dátum obdržania podpísanej zmluvy (poštou)', null=True, verbose_name='Vrátená podpísaná '),
        ),
        migrations.AddField(
            model_name='zmluvaautor',
            name='zmluva_odoslana',
            field=models.DateField(blank=True, help_text='Dátum odoslania zmluvy na podpis (poštou)', null=True, verbose_name='Odoslaná na podpis '),
        ),
        migrations.AddField(
            model_name='zmluvaautor',
            name='zmluva_vratena',
            field=models.DateField(blank=True, help_text='Dátum obdržania podpísanej zmluvy (poštou)', null=True, verbose_name='Vrátená podpísaná '),
        ),
        migrations.AlterField(
            model_name='historicalplatbaautorskasumar',
            name='obdobie',
            field=models.CharField(default='2021-11-19', help_text='Ako identifikátor vyplácania sa použije dátum jeho vytvorenia', max_length=20, verbose_name='Identifikátor vyplácania'),
        ),
        migrations.AlterField(
            model_name='historicalzmluvaautor',
            name='stav_zmluvy',
            field=models.CharField(blank=True, choices=[('odoslana_poziadavka', 'Odoslaná požiadavka na sekretariát'), ('odoslany_dotaznik', 'Odoslaný dotazník autorovi'), ('vytvorena', 'Vytvorená'), ('podpisana_enu', 'Podpísaná EnÚ'), ('odoslana_autorovi', 'Odoslaná autorovi'), ('vratena_od_autora', 'Vrátená od autora'), ('zverejnena_v_crz', 'Platná / Zverejnená v CRZ'), ('neplatna', 'Neplatná / Nebola verejnená v CRZ')], help_text='<font color="#aa0000">Zvoliť aktuálny stav zmluvy</font> (po každej jeho zmene).', max_length=20),
        ),
        migrations.AlterField(
            model_name='platbaautorskasumar',
            name='obdobie',
            field=models.CharField(default='2021-11-19', help_text='Ako identifikátor vyplácania sa použije dátum jeho vytvorenia', max_length=20, verbose_name='Identifikátor vyplácania'),
        ),
        migrations.AlterField(
            model_name='zmluvaautor',
            name='stav_zmluvy',
            field=models.CharField(blank=True, choices=[('odoslana_poziadavka', 'Odoslaná požiadavka na sekretariát'), ('odoslany_dotaznik', 'Odoslaný dotazník autorovi'), ('vytvorena', 'Vytvorená'), ('podpisana_enu', 'Podpísaná EnÚ'), ('odoslana_autorovi', 'Odoslaná autorovi'), ('vratena_od_autora', 'Vrátená od autora'), ('zverejnena_v_crz', 'Platná / Zverejnená v CRZ'), ('neplatna', 'Neplatná / Nebola verejnená v CRZ')], help_text='<font color="#aa0000">Zvoliť aktuálny stav zmluvy</font> (po každej jeho zmene).', max_length=20),
        ),
    ]