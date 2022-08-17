# Generated by Django 3.2.6 on 2022-06-24 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0072_auto_20220623_1456'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalpokladna',
            name='typ_transakcie',
            field=models.CharField(choices=[('prijem_do_pokladne', 'Príjem do pokladne'), ('vystavenie_vpd', 'Vystavenie VPD')], max_length=25, null=True, verbose_name='Typ transakcie'),
        ),
        migrations.AlterField(
            model_name='pokladna',
            name='typ_transakcie',
            field=models.CharField(choices=[('prijem_do_pokladne', 'Príjem do pokladne'), ('vystavenie_vpd', 'Vystavenie VPD')], max_length=25, null=True, verbose_name='Typ transakcie'),
        ),
    ]