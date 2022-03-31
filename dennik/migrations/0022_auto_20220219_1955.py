# Generated by Django 3.2.6 on 2022-02-19 19:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dennik', '0021_auto_20220215_1920'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dokument',
            name='typdokumentu',
            field=models.CharField(blank=True, choices=[('autorskazmluva', 'Autorská zmluva'), ('vytvarnazmluva', 'Výtvarná zmluva'), ('vobjednavka', 'Výtvarná objednávka'), ('objednavka', 'Objednávka'), ('faktura', 'Faktúra'), ('pstravne', 'Príspevok na stravné'), ('zmluva', 'Zmluva'), ('dovp', 'DoVP'), ('dopc', 'DoPC'), ('dobps', 'DoBPS'), ('hromadny', 'Hromadný dokument'), ('vyplacanie_ah', 'Vyplácanie autorských honorárov'), ('iny', 'Iný')], help_text='Uveďte typ dokumentu. <strong>Netreba vypĺňať, ak je v poli Súvisiaca položka uvedená položka databázy v tvare X-RRRR-NNN</strong>.', max_length=20, null=True, verbose_name='Typ dokumentu'),
        ),
        migrations.AlterField(
            model_name='historicaldokument',
            name='typdokumentu',
            field=models.CharField(blank=True, choices=[('autorskazmluva', 'Autorská zmluva'), ('vytvarnazmluva', 'Výtvarná zmluva'), ('vobjednavka', 'Výtvarná objednávka'), ('objednavka', 'Objednávka'), ('faktura', 'Faktúra'), ('pstravne', 'Príspevok na stravné'), ('zmluva', 'Zmluva'), ('dovp', 'DoVP'), ('dopc', 'DoPC'), ('dobps', 'DoBPS'), ('hromadny', 'Hromadný dokument'), ('vyplacanie_ah', 'Vyplácanie autorských honorárov'), ('iny', 'Iný')], help_text='Uveďte typ dokumentu. <strong>Netreba vypĺňať, ak je v poli Súvisiaca položka uvedená položka databázy v tvare X-RRRR-NNN</strong>.', max_length=20, null=True, verbose_name='Typ dokumentu'),
        ),
    ]