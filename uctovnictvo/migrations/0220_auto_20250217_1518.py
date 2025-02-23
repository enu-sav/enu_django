# Generated by Django 3.2.4 on 2025-02-17 15:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0219_auto_20250211_2011'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalodmenaoprava',
            name='zamestnanec',
            field=models.ForeignKey(blank=True, db_constraint=False, help_text="Nevypĺňa sa, ak sa vkladá súbor so zoznamom odmien alebo ak zamestnanec/dohodár nie je určený (napr. v prípade 'Oprava zrážky - plat (len pre čerpanie rozpočtu)'.", null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.zamestnanecdohodar', verbose_name='Zamestnanec/Dohodár'),
        ),
        migrations.AlterField(
            model_name='odmenaoprava',
            name='zamestnanec',
            field=models.ForeignKey(blank=True, help_text="Nevypĺňa sa, ak sa vkladá súbor so zoznamom odmien alebo ak zamestnanec/dohodár nie je určený (napr. v prípade 'Oprava zrážky - plat (len pre čerpanie rozpočtu)'.", null=True, on_delete=django.db.models.deletion.PROTECT, related_name='odmenaoprava_zamestnanec', to='uctovnictvo.zamestnanecdohodar', verbose_name='Zamestnanec/Dohodár'),
        ),
    ]
