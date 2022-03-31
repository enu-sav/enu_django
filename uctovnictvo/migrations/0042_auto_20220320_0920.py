# Generated by Django 3.2.6 on 2022-03-20 09:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0041_auto_20220310_1355'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='historicalrozhodnutie',
            options={'get_latest_by': 'history_date', 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical Rozhodnutie / Povolenie'},
        ),
        migrations.AlterModelOptions(
            name='rozhodnutie',
            options={'verbose_name': 'Rozhodnutie / Povolenie', 'verbose_name_plural': 'Faktúry - Rozhodnutia a povolenia'},
        ),
    ]