# Generated by Django 3.2.6 on 2022-10-12 12:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0090_auto_20221011_1031'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalplatovyvymer',
            name='zmena_zdroja',
            field=models.TextField(blank=True, help_text="Zadajte po riadkoch mesiace (v rozsahu platnosti výmeru), v ktorých sa zdroj odlišuje od preddefinovaného zdroja.<br /> Napr. ak je preddefinovaný zdroj 111, ale vo februári 2022 sa vyplácalo zo zdroja 42, na riadku uveďte '2022/02 42'.", max_length=500, null=True, verbose_name='Zmena zdroja'),
        ),
        migrations.AddField(
            model_name='platovyvymer',
            name='zmena_zdroja',
            field=models.TextField(blank=True, help_text="Zadajte po riadkoch mesiace (v rozsahu platnosti výmeru), v ktorých sa zdroj odlišuje od preddefinovaného zdroja.<br /> Napr. ak je preddefinovaný zdroj 111, ale vo februári 2022 sa vyplácalo zo zdroja 42, na riadku uveďte '2022/02 42'.", max_length=500, null=True, verbose_name='Zmena zdroja'),
        ),
    ]
