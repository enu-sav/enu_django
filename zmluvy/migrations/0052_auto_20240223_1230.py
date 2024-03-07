# Generated by Django 3.2.4 on 2024-02-23 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zmluvy', '0051_auto_20240223_1211'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalvytvarnaobjednavkaplatba',
            name='datum_objednavky',
            field=models.DateField(blank='True', help_text='Dátum odoslania objednávky autorovi (mailom)', null=True, verbose_name='Objednávka odoslaná'),
        ),
        migrations.AlterField(
            model_name='vytvarnaobjednavkaplatba',
            name='datum_objednavky',
            field=models.DateField(blank='True', help_text='Dátum odoslania objednávky autorovi (mailom)', null=True, verbose_name='Objednávka odoslaná'),
        ),
    ]