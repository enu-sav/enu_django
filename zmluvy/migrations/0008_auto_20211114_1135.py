# Generated by Django 3.2.6 on 2021-11-14 11:35

from django.db import migrations, models
import zmluvy.models


class Migration(migrations.Migration):

    dependencies = [
        ('zmluvy', '0007_auto_20211113_1348'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalplatbaautorskasumar',
            name='kryci_list_odoslany',
            field=models.DateField(blank=True, help_text='Dátum odoslania hárku <em>Krycí list</en> účtovníčke (internou poštou)', null=True, verbose_name="'Krycí list' odoslaný"),
        ),
        migrations.AddField(
            model_name='historicalplatbaautorskasumar',
            name='na_vyplatenie_odoslane',
            field=models.DateField(blank=True, help_text='Dátum odoslania hárku <em>Na vyplatenie</en> účtovníčke (mailom)', null=True, verbose_name="'Na vyplatenie' odoslané"),
        ),
        migrations.AddField(
            model_name='historicalplatbaautorskasumar',
            name='podklady_odoslane',
            field=models.DateField(blank=True, help_text='Dátum odoslania podkladov na vyplatenie účtovníčke', null=True, verbose_name='Podklady odoslané'),
        ),
        migrations.AddField(
            model_name='platbaautorskasumar',
            name='kryci_list_odoslany',
            field=models.DateField(blank=True, help_text='Dátum odoslania hárku <em>Krycí list</en> účtovníčke (internou poštou)', null=True, verbose_name="'Krycí list' odoslaný"),
        ),
        migrations.AddField(
            model_name='platbaautorskasumar',
            name='na_vyplatenie_odoslane',
            field=models.DateField(blank=True, help_text='Dátum odoslania hárku <em>Na vyplatenie</en> účtovníčke (mailom)', null=True, verbose_name="'Na vyplatenie' odoslané"),
        ),
        migrations.AddField(
            model_name='platbaautorskasumar',
            name='podklady_odoslane',
            field=models.DateField(blank=True, help_text='Dátum odoslania podkladov na vyplatenie účtovníčke', null=True, verbose_name='Podklady odoslané'),
        ),
        migrations.AlterField(
            model_name='historicalplatbaautorskasumar',
            name='autori_na_vyplatenie',
            field=models.TextField(blank=True, help_text="Zoznam vyplácaných autorov. Vypĺňa sa automaticky akciou 'Vytvoriť podklady na vyplatenie autorských odmien pre THS'. <br .><strong>Pokiaľ platba autora neprešla, pred vytvorením finálneho prehľadu platieb ho zo zoznamu odstráňte</strong>.", max_length=2500, null=True, verbose_name='Vyplácaní autori'),
        ),
        migrations.AlterField(
            model_name='historicalplatbaautorskasumar',
            name='datum_importovania',
            field=models.DateField(blank=True, help_text='Dátum importovania do RS/WEBRS', null=True, verbose_name='Importované do RS/WEBRS'),
        ),
        migrations.AlterField(
            model_name='historicalplatbaautorskasumar',
            name='datum_oznamenia',
            field=models.DateField(blank=True, help_text='Dátum oznámenia nezdanených autorov na finančnú správu (termín: do 15. dňa nasledujýceho mesiaca).', null=True, verbose_name='Oznámené FS (mesačné)'),
        ),
        migrations.AlterField(
            model_name='historicalplatbaautorskasumar',
            name='datum_uhradenia',
            field=models.DateField(blank=True, help_text='Dátum vyplatenia honorárov (oznámený účtovníčkou)', null=True, verbose_name='Vyplatené THS-kou'),
        ),
        migrations.AlterField(
            model_name='historicalplatbaautorskasumar',
            name='datum_zalozenia',
            field=models.DateField(blank=True, help_text='Dátum založenia hárku <em>Po autoroch</em> do šanonov.', null=True, verbose_name='Založené do šanonov (po autoroch)'),
        ),
        migrations.AlterField(
            model_name='historicalplatbaautorskasumar',
            name='import_rs',
            field=models.TextField(blank=True, help_text='Súbor s údajmi o vyplácaní na importovanie do knižného redakčného systému. Po importovaní vyplniť pole <em>Importované do RS/WEBRS</em>.', max_length=100, null=True, verbose_name='Importovať do RS'),
        ),
        migrations.AlterField(
            model_name='historicalplatbaautorskasumar',
            name='import_webrs',
            field=models.TextField(blank=True, help_text='Súbor s údajmi o vyplácaní na importovanie do webového redakčného systému. Po importovaní vyplniť pole <em>Importované do RS/WEBRS</em>.', max_length=100, null=True, verbose_name='Importovať do WEBRS'),
        ),
        migrations.AlterField(
            model_name='historicalplatbaautorskasumar',
            name='obdobie',
            field=models.CharField(default='2021-11-14', help_text='Ako identifikátor vyplácania sa použije dátum jeho vytvorenia', max_length=20, verbose_name='Identifikátor vyplácania'),
        ),
        migrations.AlterField(
            model_name='historicalplatbaautorskasumar',
            name='vyplatene',
            field=models.TextField(blank=True, help_text="Súbor je generovaný akciou 'Vytvoriť finálny prehľad o vyplácaní a zaznamenať platby do databázy'.<br .><strong>Hárok <em>Na vyplatenie</em> treba poslať mailom účtovníčke na vyplatenie</strong><br .><strong>Hárok <em>Krycí list</em> treba poslať internou poštou na THS</strong><br .> <strong>Hárok <em>Po autoroch</em> treba vytlačiť a po autoroch založiť so šanonov</strong>.", max_length=100, null=True, verbose_name='Finálny prehľad'),
        ),
        migrations.AlterField(
            model_name='historicalplatbaautorskasumar',
            name='vyplatit_ths',
            field=models.TextField(blank=True, help_text="Súbor je generovaný akciou 'Vytvoriť podklady na vyplatenie autorských odmien pre THS'. <br .>Súbor obsahuje údaje pre vyplácanie autorov (hárok <em>Na vyplatenie</em>) a zoznam chýb, ktoré boli pre generovaní zistené (hárok <em>Chyby</em>).<br /> <strong>Definitívnu verziu súboru (len hárku  <em>Na vyplatenie</em>) treba poslať mailom účtovníčke na vyplatenie.</strong>", max_length=100, null=True, verbose_name='Podklady na vyplatenie'),
        ),
        migrations.AlterField(
            model_name='platbaautorskasumar',
            name='autori_na_vyplatenie',
            field=models.TextField(blank=True, help_text="Zoznam vyplácaných autorov. Vypĺňa sa automaticky akciou 'Vytvoriť podklady na vyplatenie autorských odmien pre THS'. <br .><strong>Pokiaľ platba autora neprešla, pred vytvorením finálneho prehľadu platieb ho zo zoznamu odstráňte</strong>.", max_length=2500, null=True, verbose_name='Vyplácaní autori'),
        ),
        migrations.AlterField(
            model_name='platbaautorskasumar',
            name='datum_importovania',
            field=models.DateField(blank=True, help_text='Dátum importovania do RS/WEBRS', null=True, verbose_name='Importované do RS/WEBRS'),
        ),
        migrations.AlterField(
            model_name='platbaautorskasumar',
            name='datum_oznamenia',
            field=models.DateField(blank=True, help_text='Dátum oznámenia nezdanených autorov na finančnú správu (termín: do 15. dňa nasledujýceho mesiaca).', null=True, verbose_name='Oznámené FS (mesačné)'),
        ),
        migrations.AlterField(
            model_name='platbaautorskasumar',
            name='datum_uhradenia',
            field=models.DateField(blank=True, help_text='Dátum vyplatenia honorárov (oznámený účtovníčkou)', null=True, verbose_name='Vyplatené THS-kou'),
        ),
        migrations.AlterField(
            model_name='platbaautorskasumar',
            name='datum_zalozenia',
            field=models.DateField(blank=True, help_text='Dátum založenia hárku <em>Po autoroch</em> do šanonov.', null=True, verbose_name='Založené do šanonov (po autoroch)'),
        ),
        migrations.AlterField(
            model_name='platbaautorskasumar',
            name='import_rs',
            field=models.FileField(blank=True, help_text='Súbor s údajmi o vyplácaní na importovanie do knižného redakčného systému. Po importovaní vyplniť pole <em>Importované do RS/WEBRS</em>.', null=True, upload_to=zmluvy.models.platba_autorska_sumar_upload_location, verbose_name='Importovať do RS'),
        ),
        migrations.AlterField(
            model_name='platbaautorskasumar',
            name='import_webrs',
            field=models.FileField(blank=True, help_text='Súbor s údajmi o vyplácaní na importovanie do webového redakčného systému. Po importovaní vyplniť pole <em>Importované do RS/WEBRS</em>.', null=True, upload_to=zmluvy.models.platba_autorska_sumar_upload_location, verbose_name='Importovať do WEBRS'),
        ),
        migrations.AlterField(
            model_name='platbaautorskasumar',
            name='obdobie',
            field=models.CharField(default='2021-11-14', help_text='Ako identifikátor vyplácania sa použije dátum jeho vytvorenia', max_length=20, verbose_name='Identifikátor vyplácania'),
        ),
        migrations.AlterField(
            model_name='platbaautorskasumar',
            name='vyplatene',
            field=models.FileField(blank=True, help_text="Súbor je generovaný akciou 'Vytvoriť finálny prehľad o vyplácaní a zaznamenať platby do databázy'.<br .><strong>Hárok <em>Na vyplatenie</em> treba poslať mailom účtovníčke na vyplatenie</strong><br .><strong>Hárok <em>Krycí list</em> treba poslať internou poštou na THS</strong><br .> <strong>Hárok <em>Po autoroch</em> treba vytlačiť a po autoroch založiť so šanonov</strong>.", null=True, upload_to=zmluvy.models.platba_autorska_sumar_upload_location, verbose_name='Finálny prehľad'),
        ),
        migrations.AlterField(
            model_name='platbaautorskasumar',
            name='vyplatit_ths',
            field=models.FileField(blank=True, help_text="Súbor je generovaný akciou 'Vytvoriť podklady na vyplatenie autorských odmien pre THS'. <br .>Súbor obsahuje údaje pre vyplácanie autorov (hárok <em>Na vyplatenie</em>) a zoznam chýb, ktoré boli pre generovaní zistené (hárok <em>Chyby</em>).<br /> <strong>Definitívnu verziu súboru (len hárku  <em>Na vyplatenie</em>) treba poslať mailom účtovníčke na vyplatenie.</strong>", null=True, upload_to=zmluvy.models.platba_autorska_sumar_upload_location, verbose_name='Podklady na vyplatenie'),
        ),
    ]