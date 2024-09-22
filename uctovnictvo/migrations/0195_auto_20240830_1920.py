# Generated by Django 3.2.4 on 2024-08-30 19:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0194_auto_20240828_1506'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalobjednavka',
            name='datum_odoslania',
            field=models.DateField(blank=True, help_text='Zadajte dátum odoslania objednávky dodávateľovi. Po zadaní dátumu sa vytvorí záznam v Denníku prijatej a odoslanej pošty', null=True, verbose_name='Dátum odoslania'),
        ),
        migrations.AlterField(
            model_name='historicalobjednavka',
            name='objednane_polozky',
            field=models.TextField(help_text='<p>Na vytvorenie žiadanky (krok 1) vložte text žiadanky (voľný text). Na vytvorenie objednávky (krok 2) po riadkoch zadajte objednávané položky:</p>                <ol>                <li>možnosť: s 5 poľami oddelenými bodkočiarkou alebo lomkou / v poradí: <b>názov položky</b> / <b>merná jednotka</b> - ks, kg, l, m, m2, m3 / <b>množstvo</b> / <b>cena za jednotku bez DPH / CPV kód</b>, napr. <strong>Euroobal A4 / bal / 10 / 7,50 / 30193300-1</strong>. <br />Cena za jednotlivé položky a celková suma sa dopočíta. Pri výpočte sa berie do úvahy, či dodávateľ účtuje alebo neúčtuje cenu s DPH. </li>                <li>možnosť: ako jednoduchý text s jednou bodkočiarkou alebo lomkou, za ktorou nasleduje CPV kód, napr. <strong>Objednávame tovar podľa  priloženého zoznamu; 45321000-3</strong>.<br />Súbor takejto ponuky alebo zoznamu vložte do poľa <em>Súbor prílohy</em> a <strong>predpokladanú cenu bez DPH</strong> vložte do poľa <em>Predpokladaná cena</em>.</li>                </ol>', max_length=5000, null=True, verbose_name='Text žiadanky / Objednané položky'),
        ),
        migrations.AlterField(
            model_name='historicalobjednavka',
            name='predpokladana_cena',
            field=models.DecimalField(decimal_places=2, help_text='Zadajte predpokladanú cenu bez DPH.<br />                    Ak sú cenové údaje zadané v poli <em>Objednané položky</em>, tak hodnota v tomto poli sa podľa nich vypočíta a aktualizuje. <br />                    Vo vygenerovanej objednávke sa zoberie do úvahy, či dodávateľ účtuje alebo neúčtuje cenu s DPH.', max_digits=8, null=True, verbose_name='Predpokladaná cena'),
        ),
        migrations.AlterField(
            model_name='objednavka',
            name='datum_odoslania',
            field=models.DateField(blank=True, help_text='Zadajte dátum odoslania objednávky dodávateľovi. Po zadaní dátumu sa vytvorí záznam v Denníku prijatej a odoslanej pošty', null=True, verbose_name='Dátum odoslania'),
        ),
        migrations.AlterField(
            model_name='objednavka',
            name='objednane_polozky',
            field=models.TextField(help_text='<p>Na vytvorenie žiadanky (krok 1) vložte text žiadanky (voľný text). Na vytvorenie objednávky (krok 2) po riadkoch zadajte objednávané položky:</p>                <ol>                <li>možnosť: s 5 poľami oddelenými bodkočiarkou alebo lomkou / v poradí: <b>názov položky</b> / <b>merná jednotka</b> - ks, kg, l, m, m2, m3 / <b>množstvo</b> / <b>cena za jednotku bez DPH / CPV kód</b>, napr. <strong>Euroobal A4 / bal / 10 / 7,50 / 30193300-1</strong>. <br />Cena za jednotlivé položky a celková suma sa dopočíta. Pri výpočte sa berie do úvahy, či dodávateľ účtuje alebo neúčtuje cenu s DPH. </li>                <li>možnosť: ako jednoduchý text s jednou bodkočiarkou alebo lomkou, za ktorou nasleduje CPV kód, napr. <strong>Objednávame tovar podľa  priloženého zoznamu; 45321000-3</strong>.<br />Súbor takejto ponuky alebo zoznamu vložte do poľa <em>Súbor prílohy</em> a <strong>predpokladanú cenu bez DPH</strong> vložte do poľa <em>Predpokladaná cena</em>.</li>                </ol>', max_length=5000, null=True, verbose_name='Text žiadanky / Objednané položky'),
        ),
        migrations.AlterField(
            model_name='objednavka',
            name='predpokladana_cena',
            field=models.DecimalField(decimal_places=2, help_text='Zadajte predpokladanú cenu bez DPH.<br />                    Ak sú cenové údaje zadané v poli <em>Objednané položky</em>, tak hodnota v tomto poli sa podľa nich vypočíta a aktualizuje. <br />                    Vo vygenerovanej objednávke sa zoberie do úvahy, či dodávateľ účtuje alebo neúčtuje cenu s DPH.', max_digits=8, null=True, verbose_name='Predpokladaná cena'),
        ),
    ]