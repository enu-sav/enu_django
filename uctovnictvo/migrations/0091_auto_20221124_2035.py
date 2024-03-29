# Generated by Django 3.2.6 on 2022-11-24 20:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0090_auto_20221011_1031'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalzmluva',
            name='platna_do',
            field=models.DateField(blank=True, help_text='Zadajte dátum ukončenia platnosti trvalej zmluvy. Platnosť trvalej zmluvy sa testuje pri vytváraní faktúry.', null=True, verbose_name='Platná do'),
        ),
        migrations.AddField(
            model_name='zmluva',
            name='platna_do',
            field=models.DateField(blank=True, help_text='Zadajte dátum ukončenia platnosti trvalej zmluvy. Platnosť trvalej zmluvy sa testuje pri vytváraní faktúry.', null=True, verbose_name='Platná do'),
        ),
    ]
