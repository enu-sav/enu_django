# Generated by Django 3.2.6 on 2021-11-09 13:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0008_auto_20211106_0934'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalplatovyvymer',
            name='datum_postup',
            field=models.DateField(help_text="Dátum najbližšieho platového postupu. Pole sa vyplňuje automaticky, ak je pole 'Dátum do' nie je vyplnené, inak je prázdne", null=True, verbose_name='Dátum pl. postupu'),
        ),
        migrations.AddField(
            model_name='platovyvymer',
            name='datum_postup',
            field=models.DateField(help_text="Dátum najbližšieho platového postupu. Pole sa vyplňuje automaticky, ak je pole 'Dátum do' nie je vyplnené, inak je prázdne", null=True, verbose_name='Dátum pl. postupu'),
        ),
        migrations.AlterField(
            model_name='historicalobjednavka',
            name='termin_dodania',
            field=models.CharField(blank=True, help_text='Určite termín dodania (dátum alebo slovné určenie)', max_length=30, null=True, verbose_name='Termím dodania'),
        ),
        migrations.AlterField(
            model_name='historicalplatovyvymer',
            name='praxdni',
            field=models.IntegerField(blank=True, help_text="Pole sa vyplňuje automaticky. Ak je pole 'Dátum do' prázdne, tak toto pole obsahuje počet dní praxe neúplného posledného roku do začiatku platnosti tohoto výmeru. Ak je pole 'Dátum do' vyplnené, tak toto pole obsahuje počet dní praxe do konca platnosti tohoto výmeru.", null=True, verbose_name='Prax (dni)'),
        ),
        migrations.AlterField(
            model_name='historicalplatovyvymer',
            name='zamestnaniedni',
            field=models.IntegerField(blank=True, help_text="Pole sa vyplňuje automaticky, ak je pole 'Dátum do' vyplnené. Vtedy toto pole obsahuje počet dní zamestnania neúplného posledného roku do konca platnosti tohoto výmeru.", null=True, verbose_name='Doba zamestnania v EnÚ (dni)'),
        ),
        migrations.AlterField(
            model_name='objednavka',
            name='termin_dodania',
            field=models.CharField(blank=True, help_text='Určite termín dodania (dátum alebo slovné určenie)', max_length=30, null=True, verbose_name='Termím dodania'),
        ),
        migrations.AlterField(
            model_name='platovyvymer',
            name='praxdni',
            field=models.IntegerField(blank=True, help_text="Pole sa vyplňuje automaticky. Ak je pole 'Dátum do' prázdne, tak toto pole obsahuje počet dní praxe neúplného posledného roku do začiatku platnosti tohoto výmeru. Ak je pole 'Dátum do' vyplnené, tak toto pole obsahuje počet dní praxe do konca platnosti tohoto výmeru.", null=True, verbose_name='Prax (dni)'),
        ),
        migrations.AlterField(
            model_name='platovyvymer',
            name='zamestnaniedni',
            field=models.IntegerField(blank=True, help_text="Pole sa vyplňuje automaticky, ak je pole 'Dátum do' vyplnené. Vtedy toto pole obsahuje počet dní zamestnania neúplného posledného roku do konca platnosti tohoto výmeru.", null=True, verbose_name='Doba zamestnania v EnÚ (dni)'),
        ),
    ]
