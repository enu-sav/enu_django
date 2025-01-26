# Generated by Django 3.2.4 on 2025-01-16 13:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0213_auto_20241230_1158'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaltypzakazky',
            name='zdroj',
            field=models.ForeignKey(blank=True, db_constraint=False, help_text='Zdroj, ku ktorému je zákazka priradená', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.zdroj'),
        ),
        migrations.AddField(
            model_name='typzakazky',
            name='zdroj',
            field=models.ForeignKey(help_text='Zdroj, ku ktorému je zákazka priradená', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='typzakazky_zakazka', to='uctovnictvo.zdroj'),
        ),
    ]