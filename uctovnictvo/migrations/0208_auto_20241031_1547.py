# Generated by Django 3.2.4 on 2024-10-31 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0207_auto_20241031_1450'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalobjednavka',
            name='datum_ziadanky',
            field=models.DateField(blank=True, help_text='Zadajte dátum založenia podpísanej žiadanky do šanonu', null=True, verbose_name='Žiadanka do šanonu'),
        ),
        migrations.AddField(
            model_name='historicalobjednavka',
            name='zamietnute',
            field=models.CharField(blank=True, choices=[('ano', 'Áno'), ('nie', 'Nie')], help_text="Uveďte 'Áno', ak bola žiadanka zamietnutá. V tom prípade uveďte dôvod v poli Poznámka", max_length=3, null=True, verbose_name='Zamietnuté'),
        ),
        migrations.AddField(
            model_name='objednavka',
            name='datum_ziadanky',
            field=models.DateField(blank=True, help_text='Zadajte dátum založenia podpísanej žiadanky do šanonu', null=True, verbose_name='Žiadanka do šanonu'),
        ),
        migrations.AddField(
            model_name='objednavka',
            name='zamietnute',
            field=models.CharField(blank=True, choices=[('ano', 'Áno'), ('nie', 'Nie')], help_text="Uveďte 'Áno', ak bola žiadanka zamietnutá. V tom prípade uveďte dôvod v poli Poznámka", max_length=3, null=True, verbose_name='Zamietnuté'),
        ),
        migrations.AlterField(
            model_name='historicalnakupsuhradou',
            name='objednane_polozky',
            field=models.TextField(blank=True, help_text="<p>V prípade Žiadanky voľne popíšte požadovaný nákup.</p>                <p>V prípade Žiadosti o preplatenie zakúpené položky zadajte po riadkoch (max. 8 riadkov):</p>                <ol>                <li>Zadajte 4 polia oddelené bodkočiarkou alebo <b>lomkou /</b> v poradí: <b>názov položky a množstvo / odhadovaná cena s DPH / CPV kód</b> / EKRK, napr. <b>Euroobal A4 50 ks / 7,50 / 30193300-1 / 632003</b> CPV kód možno nahradiť pomlčkou '-'. </li>                <li>Cena tovaru/služby sa uvádza ako <b>kladná</b>, suma vrátená do pokladne ako <b>záporná</b>. </li>                <li>Po spracovaní v Softipe aktualizujte ekonomickú klasifikáciu (EKRK) tovaru podľa údajov zo Softipu.                </ol>", max_length=5000, null=True, verbose_name='Položky nákupu'),
        ),
        migrations.AlterField(
            model_name='historicalobjednavka',
            name='objednane_polozky',
            field=models.TextField(blank=True, help_text='<p>Na vytvorenie žiadanky (krok 1) vložte text žiadanky (voľný text). Na vytvorenie objednávky (krok 2) po riadkoch zadajte objednávané položky:</p>                <ol>                <li>možnosť: s 5 poľami oddelenými bodkočiarkou alebo lomkou / v poradí: <b>názov položky</b> / <b>merná jednotka</b> - ks, kg, l, m, m2, m3 / <b>množstvo</b> / <b>cena za jednotku bez DPH / CPV kód</b>, napr. <strong>Euroobal A4 / bal / 10 / 7,50 / 30193300-1</strong> <br />Cena za jednotlivé položky a celková suma sa dopočíta. Pri výpočte sa berie do úvahy, či dodávateľ účtuje alebo neúčtuje cenu s DPH. </li>                <li>možnosť: ako jednoduchý text s jednou bodkočiarkou alebo lomkou, za ktorou nasleduje CPV kód, napr. <strong>Objednávame tovar podľa  priloženého zoznamu; 45321000-3</strong>.<br />Súbor takejto ponuky alebo zoznamu vložte do poľa <em>Súbor prílohy</em> a <strong>predpokladanú cenu bez DPH</strong> vložte do poľa <em>Predpokladaná cena</em>.</li>                </ol>', max_length=5000, null=True, verbose_name='Text žiadanky / Objednané položky'),
        ),
        migrations.AlterField(
            model_name='nakupsuhradou',
            name='objednane_polozky',
            field=models.TextField(blank=True, help_text="<p>V prípade Žiadanky voľne popíšte požadovaný nákup.</p>                <p>V prípade Žiadosti o preplatenie zakúpené položky zadajte po riadkoch (max. 8 riadkov):</p>                <ol>                <li>Zadajte 4 polia oddelené bodkočiarkou alebo <b>lomkou /</b> v poradí: <b>názov položky a množstvo / odhadovaná cena s DPH / CPV kód</b> / EKRK, napr. <b>Euroobal A4 50 ks / 7,50 / 30193300-1 / 632003</b> CPV kód možno nahradiť pomlčkou '-'. </li>                <li>Cena tovaru/služby sa uvádza ako <b>kladná</b>, suma vrátená do pokladne ako <b>záporná</b>. </li>                <li>Po spracovaní v Softipe aktualizujte ekonomickú klasifikáciu (EKRK) tovaru podľa údajov zo Softipu.                </ol>", max_length=5000, null=True, verbose_name='Položky nákupu'),
        ),
        migrations.AlterField(
            model_name='objednavka',
            name='objednane_polozky',
            field=models.TextField(blank=True, help_text='<p>Na vytvorenie žiadanky (krok 1) vložte text žiadanky (voľný text). Na vytvorenie objednávky (krok 2) po riadkoch zadajte objednávané položky:</p>                <ol>                <li>možnosť: s 5 poľami oddelenými bodkočiarkou alebo lomkou / v poradí: <b>názov položky</b> / <b>merná jednotka</b> - ks, kg, l, m, m2, m3 / <b>množstvo</b> / <b>cena za jednotku bez DPH / CPV kód</b>, napr. <strong>Euroobal A4 / bal / 10 / 7,50 / 30193300-1</strong> <br />Cena za jednotlivé položky a celková suma sa dopočíta. Pri výpočte sa berie do úvahy, či dodávateľ účtuje alebo neúčtuje cenu s DPH. </li>                <li>možnosť: ako jednoduchý text s jednou bodkočiarkou alebo lomkou, za ktorou nasleduje CPV kód, napr. <strong>Objednávame tovar podľa  priloženého zoznamu; 45321000-3</strong>.<br />Súbor takejto ponuky alebo zoznamu vložte do poľa <em>Súbor prílohy</em> a <strong>predpokladanú cenu bez DPH</strong> vložte do poľa <em>Predpokladaná cena</em>.</li>                </ol>', max_length=5000, null=True, verbose_name='Text žiadanky / Objednané položky'),
        ),
    ]