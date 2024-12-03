# Generated by Django 3.2.4 on 2024-09-22 14:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0199_auto_20240921_1816'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='historicalnakupsuhradou',
            options={'get_latest_by': 'history_date', 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical Drobný nákup - Žiadanka / žiadosť'},
        ),
        migrations.AlterModelOptions(
            name='nakupsuhradou',
            options={'verbose_name': 'Drobný nákup - Žiadanka / žiadosť', 'verbose_name_plural': 'Drobný nákup / Žiadosť o obstaranie / žiadosti o preplatenie'},
        ),
        migrations.AlterField(
            model_name='historicalnakupsuhradou',
            name='cena',
            field=models.DecimalField(decimal_places=2, help_text="Cena s DPH. <br />Pri žiadanke vložiť odhadovanú cenu.<br />Pri žiadosti o preplatenie sa vypočíta z údajov v poli 'Objednane položky'", max_digits=8, null=True, verbose_name='Suma'),
        ),
        migrations.AlterField(
            model_name='historicalnakupsuhradou',
            name='forma_uhrady',
            field=models.CharField(blank=True, choices=[('hotovost', 'V hotovosti'), ('ucet', 'Na účet')], help_text='Zadáva sa až pre žiadosť o preplatenie', max_length=10, null=True, verbose_name='Forma úhrady'),
        ),
        migrations.AlterField(
            model_name='historicalnakupsuhradou',
            name='objednane_polozky',
            field=models.TextField(help_text="<p>V prípade Žiadanky voľne popíšte požadovaný nákup.</p>                <p>V prípade Žiadosti o preplatenie zakúpené položky zadajte po riadkoch (max. 8 riadkov):</p>                <ol>                <li>Zadajte 4 polia oddelené bodkočiarkou alebo <b>lomkou /</b> v poradí: <b>názov položky a množstvo / odhadovaná cena s DPH / CPV kód</b> / EKRK, napr. <b>Euroobal A4 50 ks / 7,50 / 30193300-1 / 632003</b>. CPV kód možno nahradiť pomlčkou '-'. </li>                <li>Cena tovaru/služby sa uvádza ako <b>kladná</b>, suma vrátená do pokladne ako <b>záporná</b>. </li>                <li>Po spracovaní v Softipe aktualizujte ekonomickú klasifikáciu (EKRK) tovaru podľa údajov zo Softipu.                </ol>", max_length=5000, null=True, verbose_name='Položky nákupu'),
        ),
        migrations.AlterField(
            model_name='historicalnakupsuhradou',
            name='popis',
            field=models.CharField(help_text="Zadajte stručný popis, napr. 'poštové známky'", max_length=100, verbose_name='Popis nákupu'),
        ),
        migrations.AlterField(
            model_name='historicalnakupsuhradou',
            name='ucet',
            field=models.ForeignKey(blank=True, db_constraint=False, default=1, help_text='Zadáva sa až pre žiadosť o preplatenie', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.ucetuctovnejosnovy', verbose_name='Účet'),
        ),
        migrations.AlterField(
            model_name='historicalnakupsuhradou',
            name='vybavuje',
            field=models.ForeignKey(blank=True, db_constraint=False, help_text='Osoba, ktorá veci kúpi a komu bude nákup vyúčtovaný. Zadáva sa až pre žiadosť o preplatenie', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.zamestnanecdohodar', verbose_name='Vybavuje'),
        ),
        migrations.AlterField(
            model_name='historicalnakupsuhradou',
            name='zakazka',
            field=models.ForeignKey(blank=True, db_constraint=False, help_text='Zadáva sa až pre žiadosť o preplatenie', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.typzakazky', verbose_name='Typ zákazky'),
        ),
        migrations.AlterField(
            model_name='historicalnakupsuhradou',
            name='zdroj',
            field=models.ForeignKey(blank=True, db_constraint=False, help_text='Zadáva sa až pre žiadosť o preplatenie', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.zdroj'),
        ),
        migrations.AlterField(
            model_name='historicalnakupsuhradou',
            name='ziadatel',
            field=models.ForeignKey(blank=True, db_constraint=False, help_text='Zadajte žiadateľa.', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uctovnictvo.zamestnanecdohodar', verbose_name='Žiadateľ'),
        ),
        migrations.AlterField(
            model_name='nakupsuhradou',
            name='cena',
            field=models.DecimalField(decimal_places=2, help_text="Cena s DPH. <br />Pri žiadanke vložiť odhadovanú cenu.<br />Pri žiadosti o preplatenie sa vypočíta z údajov v poli 'Objednane položky'", max_digits=8, null=True, verbose_name='Suma'),
        ),
        migrations.AlterField(
            model_name='nakupsuhradou',
            name='forma_uhrady',
            field=models.CharField(blank=True, choices=[('hotovost', 'V hotovosti'), ('ucet', 'Na účet')], help_text='Zadáva sa až pre žiadosť o preplatenie', max_length=10, null=True, verbose_name='Forma úhrady'),
        ),
        migrations.AlterField(
            model_name='nakupsuhradou',
            name='objednane_polozky',
            field=models.TextField(help_text="<p>V prípade Žiadanky voľne popíšte požadovaný nákup.</p>                <p>V prípade Žiadosti o preplatenie zakúpené položky zadajte po riadkoch (max. 8 riadkov):</p>                <ol>                <li>Zadajte 4 polia oddelené bodkočiarkou alebo <b>lomkou /</b> v poradí: <b>názov položky a množstvo / odhadovaná cena s DPH / CPV kód</b> / EKRK, napr. <b>Euroobal A4 50 ks / 7,50 / 30193300-1 / 632003</b>. CPV kód možno nahradiť pomlčkou '-'. </li>                <li>Cena tovaru/služby sa uvádza ako <b>kladná</b>, suma vrátená do pokladne ako <b>záporná</b>. </li>                <li>Po spracovaní v Softipe aktualizujte ekonomickú klasifikáciu (EKRK) tovaru podľa údajov zo Softipu.                </ol>", max_length=5000, null=True, verbose_name='Položky nákupu'),
        ),
        migrations.AlterField(
            model_name='nakupsuhradou',
            name='popis',
            field=models.CharField(help_text="Zadajte stručný popis, napr. 'poštové známky'", max_length=100, verbose_name='Popis nákupu'),
        ),
        migrations.AlterField(
            model_name='nakupsuhradou',
            name='ucet',
            field=models.ForeignKey(blank=True, default=1, help_text='Zadáva sa až pre žiadosť o preplatenie', on_delete=django.db.models.deletion.PROTECT, related_name='nakupsuhradou_nakup', to='uctovnictvo.ucetuctovnejosnovy', verbose_name='Účet'),
        ),
        migrations.AlterField(
            model_name='nakupsuhradou',
            name='vybavuje',
            field=models.ForeignKey(blank=True, help_text='Osoba, ktorá veci kúpi a komu bude nákup vyúčtovaný. Zadáva sa až pre žiadosť o preplatenie', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='nakupsuhradou_vybavuje', to='uctovnictvo.zamestnanecdohodar', verbose_name='Vybavuje'),
        ),
        migrations.AlterField(
            model_name='nakupsuhradou',
            name='zakazka',
            field=models.ForeignKey(blank=True, help_text='Zadáva sa až pre žiadosť o preplatenie', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='nakupsuhradou_nakup', to='uctovnictvo.typzakazky', verbose_name='Typ zákazky'),
        ),
        migrations.AlterField(
            model_name='nakupsuhradou',
            name='zdroj',
            field=models.ForeignKey(blank=True, help_text='Zadáva sa až pre žiadosť o preplatenie', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='nakupsuhradou_nakup', to='uctovnictvo.zdroj'),
        ),
        migrations.AlterField(
            model_name='nakupsuhradou',
            name='ziadatel',
            field=models.ForeignKey(help_text='Zadajte žiadateľa.', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='nakupsuhradou_ziadatel', to='uctovnictvo.zamestnanecdohodar', verbose_name='Žiadateľ'),
        ),
    ]