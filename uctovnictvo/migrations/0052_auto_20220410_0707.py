# Generated by Django 3.2.6 on 2022-04-10 07:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0051_cinnost_historicalcinnost'),
    ]

    operations = [
        migrations.AddField(
            model_name='dohoda',
            name='cinnost',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='dohoda_klasifikacia', to='uctovnictvo.cinnost', verbose_name='Činnosť'),
        ),
        migrations.AddField(
            model_name='historicaldobps',
            name='cinnost',
            field=models.ForeignKey(blank=True, db_constraint=False, default=1, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.cinnost', verbose_name='Činnosť'),
        ),
        migrations.AddField(
            model_name='historicaldopc',
            name='cinnost',
            field=models.ForeignKey(blank=True, db_constraint=False, default=1, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.cinnost', verbose_name='Činnosť'),
        ),
        migrations.AddField(
            model_name='historicaldovp',
            name='cinnost',
            field=models.ForeignKey(blank=True, db_constraint=False, default=1, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.cinnost', verbose_name='Činnosť'),
        ),
        migrations.AddField(
            model_name='historicalplatovyvymer',
            name='cinnost',
            field=models.ForeignKey(blank=True, db_constraint=False, default=1, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.cinnost', verbose_name='Činnosť'),
        ),
        migrations.AddField(
            model_name='historicalpravidelnaplatba',
            name='cinnost',
            field=models.ForeignKey(blank=True, db_constraint=False, default=1, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.cinnost', verbose_name='Činnosť'),
        ),
        migrations.AddField(
            model_name='historicalprijatafaktura',
            name='cinnost',
            field=models.ForeignKey(blank=True, db_constraint=False, default=1, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.cinnost', verbose_name='Činnosť'),
        ),
        migrations.AddField(
            model_name='historicalprispevoknastravne',
            name='cinnost',
            field=models.ForeignKey(blank=True, db_constraint=False, default=1, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.cinnost', verbose_name='Činnosť'),
        ),
        migrations.AddField(
            model_name='najomnefaktura',
            name='cinnost',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='najomnefaktura_klasifikacia', to='uctovnictvo.cinnost', verbose_name='Činnosť'),
        ),
        migrations.AddField(
            model_name='platovyvymer',
            name='cinnost',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='platovyvymer_klasifikacia', to='uctovnictvo.cinnost', verbose_name='Činnosť'),
        ),
        migrations.AddField(
            model_name='pravidelnaplatba',
            name='cinnost',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='pravidelnaplatba_klasifikacia', to='uctovnictvo.cinnost', verbose_name='Činnosť'),
        ),
        migrations.AddField(
            model_name='prijatafaktura',
            name='cinnost',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='prijatafaktura_klasifikacia', to='uctovnictvo.cinnost', verbose_name='Činnosť'),
        ),
        migrations.AddField(
            model_name='prispevoknastravne',
            name='cinnost',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='prispevoknastravne_klasifikacia', to='uctovnictvo.cinnost', verbose_name='Činnosť'),
        ),
    ]
