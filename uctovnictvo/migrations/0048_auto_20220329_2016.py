# Generated by Django 3.2.6 on 2022-03-29 20:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0047_auto_20220329_1748'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicalautorskyhonorar',
            name='ekoklas',
        ),
        migrations.RemoveField(
            model_name='historicalautorskyhonorar',
            name='history_user',
        ),
        migrations.RemoveField(
            model_name='historicalautorskyhonorar',
            name='program',
        ),
        migrations.RemoveField(
            model_name='historicalautorskyhonorar',
            name='zakazka',
        ),
        migrations.RemoveField(
            model_name='historicalautorskyhonorar',
            name='zdroj',
        ),
        migrations.DeleteModel(
            name='AutorskyHonorar',
        ),
        migrations.DeleteModel(
            name='HistoricalAutorskyHonorar',
        ),
    ]
