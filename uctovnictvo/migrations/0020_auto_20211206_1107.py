# Generated by Django 3.2.6 on 2021-12-06 11:07

from django.db import migrations, models
import uctovnictvo.models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0019_auto_20211206_1056'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalobjednavka',
            name='objednane_polozky',
            field=models.TextField(blank=True, help_text='<p>Po riadkoch zadajte objednávané položky:</p>                <ol>                <li>možnosť: so 4 poľami oddelenými bodkočiarkou v poradí: <b>názov položky</b>; <b>merná jednotka</b> - ks, kg, l, m, m2, m3; <b>množstvo</b>; <b>cena za jednotku bez DPH</b>, napr. <em>Euroobal A4;bal;10;7,50</em>. <br />Cena za jednotlivé položky a celková suma sa dopočíta. Pri výpočte sa berie do úvahy, či dodávateľ účtuje alebo neúčtuje cenu s DPH. </li>                <li>možnosť: ako jednoduchý text bez bodkočiarok, napr. <em>Objednávame tovar podľa priloženej ponuky / priloženého zoznamu</em> (súbor takejto ponuky alebo zoznamu vložte do poľa <em>Súbor prílohy</em>).</li>                </ol>', max_length=5000, null=True, verbose_name='Objednané položky'),
        ),
        migrations.AlterField(
            model_name='historicalobjednavka',
            name='subor_prilohy',
            field=models.TextField(blank=True, help_text='Súbor s prílohou k objednávke. Použite, ak sa v poli <em>Objednané položky</em> takáto príloha spomína.', max_length=100, null=True, verbose_name='Súbor prílohy'),
        ),
        migrations.AlterField(
            model_name='objednavka',
            name='objednane_polozky',
            field=models.TextField(blank=True, help_text='<p>Po riadkoch zadajte objednávané položky:</p>                <ol>                <li>možnosť: so 4 poľami oddelenými bodkočiarkou v poradí: <b>názov položky</b>; <b>merná jednotka</b> - ks, kg, l, m, m2, m3; <b>množstvo</b>; <b>cena za jednotku bez DPH</b>, napr. <em>Euroobal A4;bal;10;7,50</em>. <br />Cena za jednotlivé položky a celková suma sa dopočíta. Pri výpočte sa berie do úvahy, či dodávateľ účtuje alebo neúčtuje cenu s DPH. </li>                <li>možnosť: ako jednoduchý text bez bodkočiarok, napr. <em>Objednávame tovar podľa priloženej ponuky / priloženého zoznamu</em> (súbor takejto ponuky alebo zoznamu vložte do poľa <em>Súbor prílohy</em>).</li>                </ol>', max_length=5000, null=True, verbose_name='Objednané položky'),
        ),
        migrations.AlterField(
            model_name='objednavka',
            name='subor_prilohy',
            field=models.FileField(blank=True, help_text='Súbor s prílohou k objednávke. Použite, ak sa v poli <em>Objednané položky</em> takáto príloha spomína.', null=True, upload_to=uctovnictvo.models.objednavka_upload_location, verbose_name='Súbor prílohy'),
        ),
    ]
