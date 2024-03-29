# Generated by Django 3.2.4 on 2023-12-05 21:06

from django.db import migrations, models
import uctovnictvo.models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0136_auto_20231201_1629'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalnepritomnost',
            name='subor_nepritomnost_exp',
            field=models.TextField(blank=True, help_text="XLSX súbor so zoznamom neprítomností pre učtáreň.<br />Súbor sa vytvára akciou 'Exportovať neprítomnosť pre učtáreň', tak že sa zvolí riadok kde je importovaný súbor, a to za rovnaký mesiac.<br />Súbor sa vytvára z jednotlivých položiek neprítomnosti, nie z dát v importovanom súbore.", max_length=100, null=True, verbose_name='Export. súbor'),
        ),
        migrations.AddField(
            model_name='nepritomnost',
            name='subor_nepritomnost_exp',
            field=models.FileField(blank=True, help_text="XLSX súbor so zoznamom neprítomností pre učtáreň.<br />Súbor sa vytvára akciou 'Exportovať neprítomnosť pre učtáreň', tak že sa zvolí riadok kde je importovaný súbor, a to za rovnaký mesiac.<br />Súbor sa vytvára z jednotlivých položiek neprítomnosti, nie z dát v importovanom súbore.", null=True, upload_to=uctovnictvo.models.nepritomnost_upload_location, verbose_name='Export. súbor'),
        ),
        migrations.AlterField(
            model_name='historicalnepritomnost',
            name='subor_nepritomnost',
            field=models.TextField(blank=True, help_text="XLSX súbor so zoznamom neprítomností.<br />Po vložení treba akciou 'Generovať záznamy neprítomnosti' vytvoriť jednotlivé záznamy.", max_length=100, null=True, verbose_name='Import. súbor'),
        ),
        migrations.AlterField(
            model_name='nepritomnost',
            name='subor_nepritomnost',
            field=models.FileField(blank=True, help_text="XLSX súbor so zoznamom neprítomností.<br />Po vložení treba akciou 'Generovať záznamy neprítomnosti' vytvoriť jednotlivé záznamy.", null=True, upload_to=uctovnictvo.models.nepritomnost_upload_location, verbose_name='Import. súbor'),
        ),
    ]
