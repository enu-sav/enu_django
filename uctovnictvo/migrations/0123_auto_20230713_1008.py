# Generated by Django 3.2.4 on 2023-07-13 10:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0122_auto_20230616_2010'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalinternyprevod',
            name='sadzbadph',
            field=models.CharField(choices=[('20', '20 %'), ('10', '10 %'), ('5', '5 %'), ('0', '0 %')], default='20', help_text='Uveďte sadzbu DPH', max_length=10, null=True, verbose_name='Sadzba DPH'),
        ),
        migrations.AlterField(
            model_name='historicalinternyprevod',
            name='suma',
            field=models.DecimalField(decimal_places=2, max_digits=8, null=True, verbose_name='Suma'),
        ),
        migrations.AlterField(
            model_name='historicalpravidelnaplatba',
            name='sadzbadph',
            field=models.CharField(choices=[('20', '20 %'), ('10', '10 %'), ('5', '5 %'), ('0', '0 %')], default='20', help_text='Uveďte sadzbu DPH', max_length=10, null=True, verbose_name='Sadzba DPH'),
        ),
        migrations.AlterField(
            model_name='historicalpravidelnaplatba',
            name='suma',
            field=models.DecimalField(decimal_places=2, max_digits=8, null=True, verbose_name='Suma'),
        ),
        migrations.AlterField(
            model_name='historicalprijatafaktura',
            name='sadzbadph',
            field=models.CharField(choices=[('20', '20 %'), ('10', '10 %'), ('5', '5 %'), ('0', '0 %')], default='20', help_text='Uveďte sadzbu DPH', max_length=10, null=True, verbose_name='Sadzba DPH'),
        ),
        migrations.AlterField(
            model_name='historicalprijatafaktura',
            name='suma',
            field=models.DecimalField(decimal_places=2, max_digits=8, null=True, verbose_name='Suma'),
        ),
        migrations.AlterField(
            model_name='internyprevod',
            name='sadzbadph',
            field=models.CharField(choices=[('20', '20 %'), ('10', '10 %'), ('5', '5 %'), ('0', '0 %')], default='20', help_text='Uveďte sadzbu DPH', max_length=10, null=True, verbose_name='Sadzba DPH'),
        ),
        migrations.AlterField(
            model_name='internyprevod',
            name='suma',
            field=models.DecimalField(decimal_places=2, max_digits=8, null=True, verbose_name='Suma'),
        ),
        migrations.AlterField(
            model_name='pravidelnaplatba',
            name='sadzbadph',
            field=models.CharField(choices=[('20', '20 %'), ('10', '10 %'), ('5', '5 %'), ('0', '0 %')], default='20', help_text='Uveďte sadzbu DPH', max_length=10, null=True, verbose_name='Sadzba DPH'),
        ),
        migrations.AlterField(
            model_name='pravidelnaplatba',
            name='suma',
            field=models.DecimalField(decimal_places=2, max_digits=8, null=True, verbose_name='Suma'),
        ),
        migrations.AlterField(
            model_name='prijatafaktura',
            name='sadzbadph',
            field=models.CharField(choices=[('20', '20 %'), ('10', '10 %'), ('5', '5 %'), ('0', '0 %')], default='20', help_text='Uveďte sadzbu DPH', max_length=10, null=True, verbose_name='Sadzba DPH'),
        ),
        migrations.AlterField(
            model_name='prijatafaktura',
            name='suma',
            field=models.DecimalField(decimal_places=2, max_digits=8, null=True, verbose_name='Suma'),
        ),
    ]
