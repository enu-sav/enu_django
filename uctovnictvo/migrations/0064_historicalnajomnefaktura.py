# Generated by Django 3.2.6 on 2022-06-05 13:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('uctovnictvo', '0063_historicalnepritomnost'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalNajomneFaktura',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('poznamka', models.CharField(blank=True, max_length=200, null=True, verbose_name='Poznámka')),
                ('cislo', models.CharField(max_length=50, verbose_name='Číslo')),
                ('cislo_softip', models.CharField(blank=True, help_text='Zadajte číslo faktúry zo Softipu', max_length=25, null=True, verbose_name='Číslo Softip')),
                ('typ', models.CharField(choices=[('najomne', 'Nájomné'), ('sluzby', 'Služby spojené s prenájmom'), ('vyuctovanie', 'Vyúčtovanie služieb')], max_length=25, verbose_name='Typ faktúry')),
                ('dane_na_uhradu', models.DateField(blank=True, help_text='Zadajte dátum odovzdania krycieho listu na sekretariát na odoslanie THS. <br />Vytvorí sa záznam v <a href="/admin/dennik/dokument/">denníku prijatej a odoslanej pošty</a>.', null=True, verbose_name='Dané na vybavenie dňa')),
                ('splatnost_datum', models.DateField(help_text='Zadajte dátum splatnosti 1. platby v aktuálnom roku.<br />Platby sú štvrťročné, po zadaní 1. faktúry (ak nejde o vyúčtovanie) sa doplnia záznamy pre zvyšné faktúry v roku.', null=True, verbose_name='Dátum splatnosti')),
                ('suma', models.DecimalField(decimal_places=2, help_text='Zadajte sumu bez DPH štrvrťročne.<br />Ak sa nájomníkovi účtuje DPH za nájomné, vypočíta sa z tejto sumy. DPH za služby sa účtuje vždy.', max_digits=8, null=True, verbose_name='Suma bez DPH')),
                ('platobny_prikaz', models.TextField(blank=True, help_text="Súbor s krycím listom pre THS-ku. Generuje sa akciou 'Vytvoriť krycí list pre THS'.<br />Ak treba, v prípade vyúčtovania je súčasťou aj platobný prikaz", max_length=100, null=True, verbose_name='Krycí list pre THS-ku')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('cinnost', models.ForeignKey(blank=True, db_constraint=False, default=2, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.cinnost', verbose_name='Činnosť')),
                ('ekoklas', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.ekonomickaklasifikacia', verbose_name='Ekonomická klasifikácia')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('program', models.ForeignKey(blank=True, db_constraint=False, default=4, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.program')),
                ('zakazka', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.typzakazky', verbose_name='Typ zákazky')),
                ('zdroj', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.zdroj')),
                ('zmluva', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.najomnazmluva', verbose_name='Nájomná zmluva')),
            ],
            options={
                'verbose_name': 'historical Faktúra za prenájom',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]