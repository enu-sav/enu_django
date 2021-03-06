# Generated by Django 3.2.6 on 2022-06-05 13:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('uctovnictvo', '0062_nepritomnost'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalNepritomnost',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('cislo', models.CharField(max_length=50, null=True, verbose_name='Číslo')),
                ('nepritomnost_od', models.DateField(help_text='Prvý deň neprítomnosti', null=True, verbose_name='Neprítomnosť od')),
                ('nepritomnost_do', models.DateField(blank=True, help_text='Posledný deň neprítomnosti', null=True, verbose_name='Neprítomnosť do')),
                ('nepritomnost_typ', models.CharField(choices=[('materská', 'Materská'), ('ocr', 'OČR'), ('pn', 'PN'), ('dovolenka', 'Dovolenka'), ('neplatene', 'Neplatené voľno')], max_length=20, null=True, verbose_name='Typ neprítomnosti')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('zamestnanec', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.zamestnanec', verbose_name='Zamestnanec')),
            ],
            options={
                'verbose_name': 'historical Neprítomnosť',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
