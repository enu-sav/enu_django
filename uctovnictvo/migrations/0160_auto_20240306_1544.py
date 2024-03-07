# Generated by Django 3.2.4 on 2024-03-06 15:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0159_alter_objednavkazmluva_vybavuje'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalobjednavka',
            name='vybavuje',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.zamestnanecdohodar', verbose_name='Vybavuje'),
        ),
        migrations.AlterField(
            model_name='historicalobjednavkazmluva',
            name='vybavuje',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.zamestnanecdohodar', verbose_name='Vybavuje'),
        ),
        migrations.AlterField(
            model_name='historicalrozhodnutie',
            name='vybavuje',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.zamestnanecdohodar', verbose_name='Vybavuje'),
        ),
        migrations.AlterField(
            model_name='historicalzmluva',
            name='vybavuje',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.zamestnanecdohodar', verbose_name='Vybavuje'),
        ),
        migrations.AlterField(
            model_name='objednavkazmluva',
            name='vybavuje',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='objednavkazmluva_requests_created', to='uctovnictvo.zamestnanecdohodar', verbose_name='Vybavuje'),
        ),
    ]