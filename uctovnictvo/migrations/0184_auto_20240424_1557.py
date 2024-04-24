# Generated by Django 3.2.4 on 2024-04-24 15:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0183_auto_20240422_1757'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalprijatafaktura',
            name='rozpis_poloziek',
            field=models.TextField(blank=True, max_length=5000, null=True, verbose_name='Rozpis položiek'),
        ),
        migrations.AddField(
            model_name='prijatafaktura',
            name='rozpis_poloziek',
            field=models.TextField(blank=True, max_length=5000, null=True, verbose_name='Rozpis položiek'),
        ),
        migrations.AlterField(
            model_name='historicalprispevoknastravne',
            name='za_mesiac',
            field=models.CharField(choices=[('januar', 'január'), ('februar', 'február'), ('marec', 'marec'), ('april', 'apríl'), ('maj', 'máj'), ('jun', 'jún'), ('jul', 'júl'), ('august', 'august'), ('september', 'september'), ('oktober', 'október'), ('november', 'november'), ('december', 'december')], help_text="Zadajte mzdové obdobie.<br />Napr., ak dokument vytvárate koncom apríla, zvoľte 'apríl'. Zrážky za stravné sa vypočítajú za apríl a vytvorí sa zoznam príspevkov na máj.", max_length=20, null=True, verbose_name='Mesiac'),
        ),
        migrations.AlterField(
            model_name='prispevoknastravne',
            name='za_mesiac',
            field=models.CharField(choices=[('januar', 'január'), ('februar', 'február'), ('marec', 'marec'), ('april', 'apríl'), ('maj', 'máj'), ('jun', 'jún'), ('jul', 'júl'), ('august', 'august'), ('september', 'september'), ('oktober', 'október'), ('november', 'november'), ('december', 'december')], help_text="Zadajte mzdové obdobie.<br />Napr., ak dokument vytvárate koncom apríla, zvoľte 'apríl'. Zrážky za stravné sa vypočítajú za apríl a vytvorí sa zoznam príspevkov na máj.", max_length=20, null=True, verbose_name='Mesiac'),
        ),
    ]