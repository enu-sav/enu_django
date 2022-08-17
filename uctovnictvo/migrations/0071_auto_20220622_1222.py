# Generated by Django 3.2.6 on 2022-06-22 12:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0070_auto_20220621_1824'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalpokladna',
            name='datum_softip',
            field=models.DateField(blank=True, help_text="Dátum vygenerovania prehľadu výdavkov pre THS. Vypĺňa sa automaticky akciou 'Vygenerovať prehľad výdavkov pre THS'", null=True, verbose_name='Dátum THS'),
        ),
        migrations.AlterField(
            model_name='historicalpokladna',
            name='datum_transakcie',
            field=models.DateField(help_text='Dátum prijatia dotácie alebo preplatenia výdavku', null=True, verbose_name='Dátum transakcie'),
        ),
        migrations.AlterField(
            model_name='historicalpokladna',
            name='popis',
            field=models.CharField(help_text='Stručný popis transakcie.', max_length=30, null=True, verbose_name='Popis platby.'),
        ),
        migrations.AlterField(
            model_name='pokladna',
            name='datum_softip',
            field=models.DateField(blank=True, help_text="Dátum vygenerovania prehľadu výdavkov pre THS. Vypĺňa sa automaticky akciou 'Vygenerovať prehľad výdavkov pre THS'", null=True, verbose_name='Dátum THS'),
        ),
        migrations.AlterField(
            model_name='pokladna',
            name='datum_transakcie',
            field=models.DateField(help_text='Dátum prijatia dotácie alebo preplatenia výdavku', null=True, verbose_name='Dátum transakcie'),
        ),
        migrations.AlterField(
            model_name='pokladna',
            name='popis',
            field=models.CharField(help_text='Stručný popis transakcie.', max_length=30, null=True, verbose_name='Popis platby.'),
        ),
    ]