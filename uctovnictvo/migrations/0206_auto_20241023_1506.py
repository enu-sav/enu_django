# Generated by Django 3.2.4 on 2024-10-23 15:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0205_auto_20241022_2100'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalobjednavka',
            name='platba_vopred',
            field=models.CharField(blank=True, choices=[('ano', 'Áno'), ('nie', 'Nie')], help_text="Uveďte 'Áno', ak dodávateľ vyžaduje platbu vopred", max_length=3, null=True, verbose_name='Platba vopred'),
        ),
        migrations.AddField(
            model_name='objednavka',
            name='platba_vopred',
            field=models.CharField(blank=True, choices=[('ano', 'Áno'), ('nie', 'Nie')], help_text="Uveďte 'Áno', ak dodávateľ vyžaduje platbu vopred", max_length=3, null=True, verbose_name='Platba vopred'),
        ),
    ]