# Generated by Django 3.2.4 on 2023-07-16 16:44

from django.db import migrations, models
import django.db.models.deletion
import uctovnictvo.models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0125_auto_20230713_1122'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalpokladna',
            name='cinnost',
            field=models.ForeignKey(blank=True, db_constraint=False, help_text='V prípade dotácie nechajte prázdne, inak je povinné', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.cinnost', verbose_name='Činnosť'),
        ),
        migrations.AlterField(
            model_name='historicalpokladna',
            name='cislo_VPD',
            field=models.IntegerField(blank=True, null=True, verbose_name='Poradové číslo PD'),
        ),
        migrations.AlterField(
            model_name='historicalpokladna',
            name='datum_softip',
            field=models.DateField(blank=True, help_text="Dátum vytvorenia zoznamu PD pre THS. Vypĺňa sa automaticky akciou 'vytvoriť zoznam PD pre THS'", null=True, verbose_name='Dátum THS'),
        ),
        migrations.AlterField(
            model_name='historicalpokladna',
            name='ekoklas',
            field=models.ForeignKey(blank=True, db_constraint=False, help_text='V prípade dotácie nechajte prázdne, inak je povinné', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.ekonomickaklasifikacia', verbose_name='Ekonomická klasifikácia'),
        ),
        migrations.AlterField(
            model_name='historicalpokladna',
            name='popis',
            field=models.CharField(help_text='Stručný popis transakcie. Ak sa dá, v prípade PPD uveďte číslo súvisiaveho VPD', max_length=30, null=True, verbose_name='Popis platby'),
        ),
        migrations.AlterField(
            model_name='historicalpokladna',
            name='subor_vpd',
            field=models.TextField(blank=True, help_text="Súbor pokladničného dokladu (VPD, PPD). Generuje sa akciou 'Vytvoriť PD'", max_length=100, null=True, verbose_name='Súbor PD'),
        ),
        migrations.AlterField(
            model_name='historicalpokladna',
            name='typ_transakcie',
            field=models.CharField(choices=[('prijem_do_pokladne', 'Príjem do pokladne'), ('vystavenie_vpd', 'Výdavkový PD'), ('vystavenie_ppd', 'Príjmový PD')], max_length=25, null=True, verbose_name='Typ záznamu'),
        ),
        migrations.AlterField(
            model_name='historicalpokladna',
            name='zakazka',
            field=models.ForeignKey(blank=True, db_constraint=False, help_text='V prípade dotácie nechajte prázdne, inak je povinné', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.typzakazky', verbose_name='Typ zákazky'),
        ),
        migrations.AlterField(
            model_name='historicalpokladna',
            name='zdroj',
            field=models.ForeignKey(blank=True, db_constraint=False, help_text='V prípade dotácie nechajte prázdne, inak je povinné', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.zdroj'),
        ),
        migrations.AlterField(
            model_name='pokladna',
            name='cinnost',
            field=models.ForeignKey(blank=True, help_text='V prípade dotácie nechajte prázdne, inak je povinné', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='pokladna_pokladna', to='uctovnictvo.cinnost', verbose_name='Činnosť'),
        ),
        migrations.AlterField(
            model_name='pokladna',
            name='cislo_VPD',
            field=models.IntegerField(blank=True, null=True, verbose_name='Poradové číslo PD'),
        ),
        migrations.AlterField(
            model_name='pokladna',
            name='datum_softip',
            field=models.DateField(blank=True, help_text="Dátum vytvorenia zoznamu PD pre THS. Vypĺňa sa automaticky akciou 'vytvoriť zoznam PD pre THS'", null=True, verbose_name='Dátum THS'),
        ),
        migrations.AlterField(
            model_name='pokladna',
            name='ekoklas',
            field=models.ForeignKey(blank=True, help_text='V prípade dotácie nechajte prázdne, inak je povinné', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='pokladna_pokladna', to='uctovnictvo.ekonomickaklasifikacia', verbose_name='Ekonomická klasifikácia'),
        ),
        migrations.AlterField(
            model_name='pokladna',
            name='popis',
            field=models.CharField(help_text='Stručný popis transakcie. Ak sa dá, v prípade PPD uveďte číslo súvisiaveho VPD', max_length=30, null=True, verbose_name='Popis platby'),
        ),
        migrations.AlterField(
            model_name='pokladna',
            name='subor_vpd',
            field=models.FileField(blank=True, help_text="Súbor pokladničného dokladu (VPD, PPD). Generuje sa akciou 'Vytvoriť PD'", null=True, upload_to=uctovnictvo.models.pokladna_upload_location, verbose_name='Súbor PD'),
        ),
        migrations.AlterField(
            model_name='pokladna',
            name='typ_transakcie',
            field=models.CharField(choices=[('prijem_do_pokladne', 'Príjem do pokladne'), ('vystavenie_vpd', 'Výdavkový PD'), ('vystavenie_ppd', 'Príjmový PD')], max_length=25, null=True, verbose_name='Typ záznamu'),
        ),
        migrations.AlterField(
            model_name='pokladna',
            name='zakazka',
            field=models.ForeignKey(blank=True, help_text='V prípade dotácie nechajte prázdne, inak je povinné', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='pokladna_pokladna', to='uctovnictvo.typzakazky', verbose_name='Typ zákazky'),
        ),
        migrations.AlterField(
            model_name='pokladna',
            name='zdroj',
            field=models.ForeignKey(blank=True, help_text='V prípade dotácie nechajte prázdne, inak je povinné', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='pokladna_pokladna', to='uctovnictvo.zdroj'),
        ),
    ]