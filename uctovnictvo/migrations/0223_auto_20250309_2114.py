# Generated by Django 3.2.4 on 2025-03-09 21:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0222_auto_20250222_2107'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='historicalprispevoknarekreaciu',
            options={'get_latest_by': 'history_date', 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical Príspevok na rekreáciu a šport'},
        ),
        migrations.AlterModelOptions(
            name='prispevoknarekreaciu',
            options={'verbose_name': 'Príspevok na rekreáciu a šport', 'verbose_name_plural': 'PaM - Príspevky na rekreáciu a šport'},
        ),
    ]
