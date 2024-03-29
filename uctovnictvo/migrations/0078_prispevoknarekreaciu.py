# Generated by Django 3.2.6 on 2022-08-17 14:05

from django.db import migrations, models
import django.db.models.deletion
import uctovnictvo.models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0077_auto_20220810_1541'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrispevokNaRekreaciu',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('poznamka', models.CharField(blank=True, max_length=200, null=True, verbose_name='Poznámka')),
                ('cislo', models.CharField(max_length=50, null=True, verbose_name='Číslo')),
                ('datum', models.DateField(help_text='Dátum prijatia žiadosti', null=True, verbose_name='Dátum prijatia žiadosti')),
                ('subor_ziadost', models.FileField(help_text='Súbor so žiadosťou o príspevok (doručený zamestnancom).<br />Po zadaní sa vytvorí záznam v Denníku.', upload_to=uctovnictvo.models.rekreacia_upload_location, verbose_name='Žiadosť o príspevok')),
                ('subor_vyuctovanie', models.FileField(blank=True, help_text='Súbor s vyúčtovaním príspevku (doručený mzdovou účtárňou).<br />Po zadaní sa vytvorí záznam v Denníku.', null=True, upload_to=uctovnictvo.models.rekreacia_upload_location, verbose_name='Vyúčtovanie príspevku')),
                ('prispevok', models.DecimalField(blank=True, decimal_places=2, default=0, help_text='Výška príspevku na rekreáciu určená mzdovou účtárňou (záporné číslo).', max_digits=8, null=True, verbose_name='Príspevok na vyplatenie')),
                ('vyplatene_v_obdobi', models.CharField(blank=True, help_text='Uveďte obdobie vyplatenia podľa vyúčtovania v tvare MM/RRRR (napr. 07/2022)', max_length=10, null=True, verbose_name='Vyplatené v')),
                ('subor_kl', models.FileField(blank=True, help_text='Súbor s krycím listom.<br />Generuje sa akciou <em>Vytvoriť krycí list</em> po vyplnení položky <em>Príspevok na vyplatenie</em>', null=True, upload_to=uctovnictvo.models.rekreacia_upload_location, verbose_name='Krycí list')),
                ('datum_kl', models.DateField(blank=True, help_text='Dátum odoslania krycieho listu.<br />Po zadaní sa vytvorí záznam v Denníku.', null=True, verbose_name='Dátum odoslania KL')),
                ('cinnost', models.ForeignKey(default=2, on_delete=django.db.models.deletion.PROTECT, related_name='prispevoknarekreaciu_klasifikacia', to='uctovnictvo.cinnost', verbose_name='Činnosť')),
                ('ekoklas', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='prispevoknarekreaciu_klasifikacia', to='uctovnictvo.ekonomickaklasifikacia', verbose_name='Ekonomická klasifikácia')),
                ('program', models.ForeignKey(default=4, on_delete=django.db.models.deletion.PROTECT, related_name='prispevoknarekreaciu_klasifikacia', to='uctovnictvo.program')),
                ('zakazka', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='prispevoknarekreaciu_klasifikacia', to='uctovnictvo.typzakazky', verbose_name='Typ zákazky')),
                ('zamestnanec', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='prispevoknarekreaciu_zamestnanec', to='uctovnictvo.zamestnanec', verbose_name='Zamestnanec')),
                ('zdroj', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='prispevoknarekreaciu_klasifikacia', to='uctovnictvo.zdroj')),
            ],
            options={
                'verbose_name': 'Príspevok na rekreáciu',
                'verbose_name_plural': 'PaM - Príspevky na rekreáciu',
            },
        ),
    ]
