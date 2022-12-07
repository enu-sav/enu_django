# Generated by Django 3.2.6 on 2022-10-13 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0093_historicalodmenaoprava_odmenaoprava'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalodmenaoprava',
            name='suma',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Výška odmeny alebo opravy. Odmena je záporná, oprava môže byť kladná (t.j. zmestnancovi bola strhnutá z výplaty).', max_digits=8, null=True, verbose_name='Suma'),
        ),
        migrations.AlterField(
            model_name='odmenaoprava',
            name='suma',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Výška odmeny alebo opravy. Odmena je záporná, oprava môže byť kladná (t.j. zmestnancovi bola strhnutá z výplaty).', max_digits=8, null=True, verbose_name='Suma'),
        ),
    ]