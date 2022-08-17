# Generated by Django 3.2.6 on 2022-06-10 22:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('uctovnictvo', '0066_historicalrozpoctovapolozka_historicalrozpoctovapolozkadotacia_rozpoctovapolozka_rozpoctovapolozkado'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='historicalrozpoctovapolozkadotacia',
            options={'get_latest_by': 'history_date', 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical Dotácia'},
        ),
        migrations.AlterModelOptions(
            name='rozpoctovapolozkadotacia',
            options={'verbose_name': 'Dotácia', 'verbose_name_plural': 'Rozpočet - Dotácie'},
        ),
        migrations.AlterField(
            model_name='historicalrozpoctovapolozkadotacia',
            name='suma',
            field=models.DecimalField(decimal_places=2, help_text='Suma sa pripočíta k zodpovedajúcej rozpočtovej položke za aktuálny rok. Ak tá ešte neexistuje, vytvorí sa.', max_digits=8, null=True, verbose_name='Výška dotácie'),
        ),
        migrations.AlterField(
            model_name='rozpoctovapolozkadotacia',
            name='suma',
            field=models.DecimalField(decimal_places=2, help_text='Suma sa pripočíta k zodpovedajúcej rozpočtovej položke za aktuálny rok. Ak tá ešte neexistuje, vytvorí sa.', max_digits=8, null=True, verbose_name='Výška dotácie'),
        ),
        migrations.CreateModel(
            name='RozpoctovaPolozkaPresun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cislo', models.CharField(max_length=50, verbose_name='Číslo')),
                ('suma', models.DecimalField(decimal_places=2, help_text='Suma sa presunie zo zdrojovej do cieľovej rozpočtovej položky', max_digits=8, null=True, verbose_name='Suma na presunutie')),
                ('dovod', models.CharField(max_length=200, null=True, verbose_name='Dôvod presunu')),
                ('ciel', models.ForeignKey(help_text='Ak cieľová položka ešte neexistuje, vytvorte ju ako dotáciu s 0-ovou výškou.', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='rozpoctovapolozkapresun_ciel', to='uctovnictvo.rozpoctovapolozka', verbose_name='Do položky')),
                ('zdroj', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='rozpoctovapolozkapresun_zdroj', to='uctovnictvo.rozpoctovapolozka', verbose_name='Z položky')),
            ],
            options={
                'verbose_name': 'Presun medzi položkami',
                'verbose_name_plural': 'Rozpočet - Presuny',
            },
        ),
        migrations.CreateModel(
            name='HistoricalRozpoctovaPolozkaPresun',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('cislo', models.CharField(max_length=50, verbose_name='Číslo')),
                ('suma', models.DecimalField(decimal_places=2, help_text='Suma sa presunie zo zdrojovej do cieľovej rozpočtovej položky', max_digits=8, null=True, verbose_name='Suma na presunutie')),
                ('dovod', models.CharField(max_length=200, null=True, verbose_name='Dôvod presunu')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('ciel', models.ForeignKey(blank=True, db_constraint=False, help_text='Ak cieľová položka ešte neexistuje, vytvorte ju ako dotáciu s 0-ovou výškou.', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.rozpoctovapolozka', verbose_name='Do položky')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('zdroj', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.rozpoctovapolozka', verbose_name='Z položky')),
            ],
            options={
                'verbose_name': 'historical Presun medzi položkami',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]