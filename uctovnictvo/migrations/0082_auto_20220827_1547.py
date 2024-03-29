# Generated by Django 3.2.6 on 2022-08-27 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0081_auto_20220825_2129'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalnajomnefaktura',
            name='dan',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Zadajte sumu DPH štrvrťročne.<br />V prípade zmlúv uzavretých 07/2022 a neskôr sa DPH neúčtuje.', max_digits=8, null=True, verbose_name='DPH'),
        ),
        migrations.AddField(
            model_name='najomnefaktura',
            name='dan',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Zadajte sumu DPH štrvrťročne.<br />V prípade zmlúv uzavretých 07/2022 a neskôr sa DPH neúčtuje.', max_digits=8, null=True, verbose_name='DPH'),
        ),
    ]
