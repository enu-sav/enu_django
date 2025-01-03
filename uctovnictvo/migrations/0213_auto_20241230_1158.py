# Generated by Django 3.2.4 on 2024-12-30 11:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0212_auto_20241230_0951'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalinternyprevod',
            name='sadzbadph',
            field=models.CharField(choices=[('23', '23 %'), ('20', '20 %'), ('19', '19 %'), ('10', '10 %'), ('5', '5 %'), ('0', '0 %')], help_text='Uveďte sadzbu DPH.', max_length=10, null=True, verbose_name='Sadzba DPH'),
        ),
        migrations.AlterField(
            model_name='historicalpravidelnaplatba',
            name='sadzbadph',
            field=models.CharField(choices=[('23', '23 %'), ('20', '20 %'), ('19', '19 %'), ('10', '10 %'), ('5', '5 %'), ('0', '0 %')], help_text='Uveďte sadzbu DPH.', max_length=10, null=True, verbose_name='Sadzba DPH'),
        ),
        migrations.AlterField(
            model_name='historicalprijatafaktura',
            name='sadzbadph',
            field=models.CharField(choices=[('23', '23 %'), ('20', '20 %'), ('19', '19 %'), ('10', '10 %'), ('5', '5 %'), ('0', '0 %')], help_text='Uveďte sadzbu DPH.', max_length=10, null=True, verbose_name='Sadzba DPH'),
        ),
        migrations.AlterField(
            model_name='historicalvystavenafaktura',
            name='sadzbadph',
            field=models.CharField(choices=[('23', '23 %'), ('20', '20 %'), ('19', '19 %'), ('10', '10 %'), ('5', '5 %'), ('0', '0 %')], help_text='Uveďte sadzbu DPH.', max_length=10, null=True, verbose_name='Sadzba DPH'),
        ),
        migrations.AlterField(
            model_name='internyprevod',
            name='sadzbadph',
            field=models.CharField(choices=[('23', '23 %'), ('20', '20 %'), ('19', '19 %'), ('10', '10 %'), ('5', '5 %'), ('0', '0 %')], help_text='Uveďte sadzbu DPH.', max_length=10, null=True, verbose_name='Sadzba DPH'),
        ),
        migrations.AlterField(
            model_name='pravidelnaplatba',
            name='sadzbadph',
            field=models.CharField(choices=[('23', '23 %'), ('20', '20 %'), ('19', '19 %'), ('10', '10 %'), ('5', '5 %'), ('0', '0 %')], help_text='Uveďte sadzbu DPH.', max_length=10, null=True, verbose_name='Sadzba DPH'),
        ),
        migrations.AlterField(
            model_name='prijatafaktura',
            name='sadzbadph',
            field=models.CharField(choices=[('23', '23 %'), ('20', '20 %'), ('19', '19 %'), ('10', '10 %'), ('5', '5 %'), ('0', '0 %')], help_text='Uveďte sadzbu DPH.', max_length=10, null=True, verbose_name='Sadzba DPH'),
        ),
        migrations.AlterField(
            model_name='vystavenafaktura',
            name='sadzbadph',
            field=models.CharField(choices=[('23', '23 %'), ('20', '20 %'), ('19', '19 %'), ('10', '10 %'), ('5', '5 %'), ('0', '0 %')], help_text='Uveďte sadzbu DPH.', max_length=10, null=True, verbose_name='Sadzba DPH'),
        ),
    ]
