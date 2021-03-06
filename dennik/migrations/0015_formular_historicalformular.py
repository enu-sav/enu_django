# Generated by Django 3.2.6 on 2022-02-06 18:54

import dennik.models
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models
import uctovnictvo.storage


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dennik', '0014_auto_20220124_1730'),
    ]

    operations = [
        migrations.CreateModel(
            name='Formular',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('typformulara', models.CharField(choices=[('vseobecny', 'Všeobecný dokument')], help_text='Uveďte typ šablóny. Určuje, aké tokeny možno použiť:\n                <ul>\n                <li><em>Všeobecný dokument</em>: ľubovoľné tokeny, bez väzby na databázu</li>\n                </ul>', max_length=20, null=True, verbose_name='Typ šablóny')),
                ('subor_nazov', models.CharField(help_text='Krátky názov dokumentu', max_length=40, verbose_name='Názov')),
                ('subor_popis', models.TextField(blank=True, help_text='Dlhší popis k dokumentu: účel, poznámky a pod.', max_length=250, verbose_name='Popis')),
                ('na_odoslanie', models.DateField(blank=True, help_text='Zadajte dátum odovzdania vytvorených dokumentov na sekretariát na odoslanie. <br />Vytvorí sa záznam v <a href="/admin/dennik/dokument/">denníku prijatej a odoslanej pošty</a>.</br />Po odoslaní nemožno ďalej upravovať', null=True, verbose_name='Na odoslanie dňa')),
                ('sablona', models.FileField(help_text='FODT súbor šablóny na generovanie dokumentu. <br />Polia na vyplnenie musia byť definované ako [[tokeny]] s dvojitými hranatými zátvorkami.<br />Posledná strana šablóny musí byť vyplnená prázdnymi riadkami až po koniec strany. <br />Tokeny sa musia presne zhodovať s názvami stĺpcov v dátovom súbore.', null=True, storage=uctovnictvo.storage.OverwriteStorage(), upload_to=dennik.models.form_file_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['fodt'])], verbose_name='Šablóna dokumentu')),
                ('data', models.FileField(help_text="XLSX súbor s dátami na generovanie. <br />Názvy stĺpcov na vyplnenie sa musia presne zhodovať s tokenmi v šablóne (bez zátvoriek).<br />Názvy stĺpcov, ktoré majú byť formátované s dvomi des. miestami, musia začínať 'n_'.", null=True, storage=uctovnictvo.storage.OverwriteStorage(), upload_to=dennik.models.form_file_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['xlsx'])], verbose_name='Dáta')),
                ('vyplnene', models.FileField(help_text="Vytvorený súbor hromadného dokumentu vo formáte FODT (vytvorený akciou 'Vytvoriť súbor hromadného dokumentu').", null=True, storage=uctovnictvo.storage.OverwriteStorage(), upload_to=dennik.models.form_file_path, verbose_name='Vytvorený súbor')),
                ('vyplnene_data', models.FileField(help_text="XLSX súbor s dátami použitými na vytvorenie hromadného dokumentu (vytvorený akciou 'Vyplniť formulár').", null=True, storage=uctovnictvo.storage.OverwriteStorage(), upload_to=dennik.models.form_file_path, verbose_name='Vyplnené dáta')),
            ],
            options={
                'verbose_name': 'Hromadný dokument',
                'verbose_name_plural': 'Generovanie hromadných dokumentov',
            },
        ),
        migrations.CreateModel(
            name='HistoricalFormular',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('typformulara', models.CharField(choices=[('vseobecny', 'Všeobecný dokument')], help_text='Uveďte typ šablóny. Určuje, aké tokeny možno použiť:\n                <ul>\n                <li><em>Všeobecný dokument</em>: ľubovoľné tokeny, bez väzby na databázu</li>\n                </ul>', max_length=20, null=True, verbose_name='Typ šablóny')),
                ('subor_nazov', models.CharField(help_text='Krátky názov dokumentu', max_length=40, verbose_name='Názov')),
                ('subor_popis', models.TextField(blank=True, help_text='Dlhší popis k dokumentu: účel, poznámky a pod.', max_length=250, verbose_name='Popis')),
                ('na_odoslanie', models.DateField(blank=True, help_text='Zadajte dátum odovzdania vytvorených dokumentov na sekretariát na odoslanie. <br />Vytvorí sa záznam v <a href="/admin/dennik/dokument/">denníku prijatej a odoslanej pošty</a>.</br />Po odoslaní nemožno ďalej upravovať', null=True, verbose_name='Na odoslanie dňa')),
                ('sablona', models.TextField(help_text='FODT súbor šablóny na generovanie dokumentu. <br />Polia na vyplnenie musia byť definované ako [[tokeny]] s dvojitými hranatými zátvorkami.<br />Posledná strana šablóny musí byť vyplnená prázdnymi riadkami až po koniec strany. <br />Tokeny sa musia presne zhodovať s názvami stĺpcov v dátovom súbore.', max_length=100, null=True, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['fodt'])], verbose_name='Šablóna dokumentu')),
                ('data', models.TextField(help_text="XLSX súbor s dátami na generovanie. <br />Názvy stĺpcov na vyplnenie sa musia presne zhodovať s tokenmi v šablóne (bez zátvoriek).<br />Názvy stĺpcov, ktoré majú byť formátované s dvomi des. miestami, musia začínať 'n_'.", max_length=100, null=True, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['xlsx'])], verbose_name='Dáta')),
                ('vyplnene', models.TextField(help_text="Vytvorený súbor hromadného dokumentu vo formáte FODT (vytvorený akciou 'Vytvoriť súbor hromadného dokumentu').", max_length=100, null=True, verbose_name='Vytvorený súbor')),
                ('vyplnene_data', models.TextField(help_text="XLSX súbor s dátami použitými na vytvorenie hromadného dokumentu (vytvorený akciou 'Vyplniť formulár').", max_length=100, null=True, verbose_name='Vyplnené dáta')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical Hromadný dokument',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
