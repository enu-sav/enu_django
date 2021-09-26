from django.db import models

#záznam histórie
#https://django-simple-history.readthedocs.io/en/latest/admin.html
from simple_history.models import HistoricalRecords
from uctovnictvo.storage import OverwriteStorage
from polymorphic.models import PolymorphicModel

from beliana.settings import TMPLTS_DIR_NAME
import os
from datetime import datetime

class AnoNie(models.TextChoices):
    ANO = 'ano', 'Áno'
    NIE = 'nie', 'Nie'

class Mena(models.TextChoices):
    EUR = 'EUR'
    CZK = 'CZK'
    USD = 'USD'

class Zdroj(models.Model):
    kod = models.CharField("Kód", 
            help_text = "Zadajte kód zdroja - napr. 111, 46 alebo 42", 
            max_length=20)
    popis = models.CharField("Popis", 
            help_text = "Popíšte zdroj",
            max_length=100)
    def __str__(self):
        return f"{self.kod} - {self.popis}"
    class Meta:
        verbose_name = 'Zdroj'
        verbose_name_plural = 'Zdroje'

class Program(models.Model):
    kod = models.CharField("Kód", 
            help_text = "Zadajte kód programu - napr. 087060J, 0EK1102 alebo 0EK1103",
            max_length=20)
    popis = models.CharField("Popis", 
            help_text = "Popíšte program",
            max_length=100)
    def __str__(self):
        return f"{self.kod} - {self.popis}"
    class Meta:
        verbose_name = 'Program'
        verbose_name_plural = 'Programy'

class TypZakazky(models.Model):
    kod = models.CharField("Kód", 
            help_text = "Zadajte kód typu zákazky, napr. Beliana alebo Ostatné",
            max_length=20)
    popis = models.CharField("Popis", 
            help_text = "Popíšte typ zákazky",
            max_length=100)
    def __str__(self):
        return f"{self.kod} - {self.popis}"
    class Meta:
        verbose_name = 'Typ zákazky'
        verbose_name_plural = 'Typy zákazky'

class EkonomickaKlasifikacia(models.Model):
    kod = models.CharField("Kód", 
            help_text = "Zadajte kód položky/podpoložky ekonomickej klasifikácie napr. 614 alebo 632001 (bez medzery)",
            max_length=10)
    nazov = models.CharField("Názov", 
            help_text = "Zadajte názov položky/podpoložky ekonomickej klasifikácie napr. 'Granty a transfery'",
            max_length=100)
    def __str__(self):
        return f"{self.kod} - {self.nazov}"
    class Meta:
        verbose_name = 'Ekonomická klasifikácia'
        verbose_name_plural = 'Ekonomická klasifikácia'
 

# Abstraktná trieda so všetkými spoločnými poľami, nepoužívaná samostatne
class PersonCommon(models.Model):
    # IBAN alebo aj kompletný popis s BIC a číslom účtu
    bankovy_kontakt = models.CharField("Bankový kontakt", 
            help_text = "Zadajte IBAN účtu autora.",
            max_length=200, null=True, blank=True)
    adresa_ulica = models.CharField("Adresa – ulica a číslo domu", max_length=200, null=True, blank=True)
    adresa_mesto = models.CharField("Adresa – PSČ a mesto", max_length=200, null=True, blank=True)
    adresa_stat = models.CharField("Adresa – štát", max_length=100, null=True, blank=True)
    datum_aktualizacie = models.DateField('Dátum aktualizácie', auto_now=True)
    class Meta:
        abstract = True

class Dodavatel(PersonCommon):
    nazov = models.CharField("Názov", max_length=200)
    s_danou = models.CharField("Fakturované s daňou", 
            max_length=3, 
            help_text = "Uveďte 'Áno', ak dodávateľ fakturuje s DPH, inak uveďte 'Nie'",
            null = True,
            choices=AnoNie.choices)
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Dodávateľ'
        verbose_name_plural = 'Dodávatelia'
    def __str__(self):
        return self.nazov

#Polymorphic umožní, aby Objednavka a PrijataFaktura mohli použiť ObjednavkaZmluva ako ForeignKey
class ObjednavkaZmluva(PolymorphicModel):
    cislo = models.CharField("Číslo", 
            help_text = "Zadajte číslo objednávky / zmluvy / rozhodnutia. Na jednoduché rozlíšenie viacerých zmlúv toho istého dodávateľa možno v zátvorke uviesť krátku doplnkovú informáciu, napr. '2/2018 (dodávka plynu)'",
            max_length=50)
    dodavatel = models.ForeignKey(Dodavatel,
            on_delete=models.PROTECT, 
            verbose_name = "Dodávateľ",
            related_name='%(class)s_requests_created')  #zabezpečí rozlíšenie modelov Objednavka a PrijataFaktura 
    predmet = models.CharField("Predmet", 
            help_text = "Zadajte stručný popis, napr. 'Kávovar Saeco' alebo 'Servisná podpora RS Beliana'",
            max_length=100)
    poznamka = models.CharField("Poznámka", 
            max_length=200, 
            null=True,
            blank=True)
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Objednávka / zmluva'
        verbose_name_plural = 'Objednávky / zmluvy'
        #abstract = True
    def __str__(self):
        return f"{self.cislo} - {self.dodavatel}"

class Objednavka(ObjednavkaZmluva):
    objednane_polozky = models.TextField("Objednané položky", 
            help_text = "Po riadkoch zadajte položky s poľami oddelenými bodkočiarkou: Názov položky; merná jednotka (ks, kg, l, m, m2, m3,...); Množstvo; Cena za jednotku bez DPH",
            max_length=5000, null=True, blank=True)
    datum_vytvorenia = models.DateField('Dátum vytvorenia',
            help_text = "Zadajte dátum vytvorenia objednávky",
            default=datetime.now,
            blank=True, null=True)
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Objednávka'
        verbose_name_plural = 'Objednávky'
    def __str__(self):
        return f"{self.dodavatel}, objednávka, {self.cislo}"

class Rozhodnutie(ObjednavkaZmluva):
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Rozhodnutie'
        verbose_name_plural = 'Rozhodnutia'
    def __str__(self):
        return f"{self.dodavatel}, rozhodnutie, {self.cislo}"

class Zmluva(ObjednavkaZmluva):
    url_zmluvy = models.URLField('URL zmluvy', 
            help_text = "Zadajte URL pdf súboru zmluvy zo stránky CRZ.",
            blank = True)
    datum_zverejnenia_CRZ = models.DateField('Platná od', 
            help_text = "Zadajte dátum účinnosti zmluvy (dátum zverejnenia v CRZ + 1 deň).",
            blank=True, null=True)
    trvala_zmluva = models.CharField("Trvalá zmluva", 
            max_length=3, 
            help_text = "Uveďte 'Áno', ak ide o trvalú zmluvu (očakáva sa viacero faktúr), inak uveďte 'Nie' (ako napr. zmluvy s LITA)",
            default = AnoNie.ANO,
            choices=AnoNie.choices)
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Zmluva'
        verbose_name_plural = 'Zmluvy'
    def __str__(self):
        return f"{self.dodavatel}, zmluva, {self.cislo}"
 
class Klasifikacia(models.Model):
    zdroj = models.ForeignKey(Zdroj,
            on_delete=models.PROTECT,
            related_name='%(class)s_klasifikacia')  # (class)s zabezpečí rozlíšenie modelov v poli objednavka_zmluva triedy PrijataFaktura
                                                    # s za zatvorkou je povinne
    program = models.ForeignKey(Program,
            on_delete=models.PROTECT,
            related_name='%(class)s_klasifikacia')
    zakazka = models.ForeignKey(TypZakazky,
            on_delete=models.PROTECT,
            verbose_name = "Typ zákazky",
            related_name='%(class)s_klasifikacia')
    ekoklas = models.ForeignKey(EkonomickaKlasifikacia,
            on_delete=models.PROTECT,
            verbose_name = "Ekonomická klasifikácia",
            related_name='%(class)s_klasifikacia')
    poznamka = models.CharField("Poznámka", max_length=200, blank=True)
    class Meta:
        abstract = True

#https://stackoverflow.com/questions/55543232/how-to-upload-multiple-files-from-the-django-admin
#Vykoná sa len pri vkladaní suborov cez GUI. Pri programovom vytváraní treba cestu nastaviť
def platobny_prikaz_upload_location(instance, filename):
    trace()
    pass
    return filename

class PrijataFaktura(Klasifikacia):
    cislo = models.CharField("Číslo faktúry", max_length=50)
    dcislo = models.CharField("Dodávateľské číslo faktúry", 
            blank=True, 
            null=True,
            max_length=50)
    doslo_datum = models.DateField('Došlo dňa',
            blank=True, null=True)
    dane_na_uhradu = models.DateField('Dané na úhradu dňa',
            blank=True, null=True)
    splatnost_datum = models.DateField('Dátum splatnosti',
            blank=True, null=True)
    predmet = models.CharField("Predmet faktúry", 
            help_text = "Zadajte stručný popis, napr. 'Dodávka a inštalácia dátoveho rozvádzača'",
            max_length=100)
    suma = models.DecimalField("Suma v EUR", 
            help_text = "Zadajte príjmy ako kladné, výdavky ako záporné číslo",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    mena = models.CharField("Mena", 
            max_length=3, 
            default= Mena.EUR,
            choices=Mena.choices)
    objednavka_zmluva = models.ForeignKey(ObjednavkaZmluva, 
            null=True, 
            verbose_name = "Objednávka / zmluva",
            on_delete=models.PROTECT, 
            related_name='faktury')    
    platobny_prikaz = models.FileField("Platobný príkaz pre THS-ku",
            help_text = "Súbor s platobným príkazom a krycím listom pre THS-ku. Generuje sa akciou 'Vytvoriť platobný príkaz a krycí list príkaz pre THS'",
            upload_to=platobny_prikaz_upload_location, 
            null = True, blank = True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Prijatá faktúra'
        verbose_name_plural = 'Prijaté faktúry'
    def __str__(self):
        return f'Faktúra k "{self.objednavka_zmluva}" : {self.suma} €'

class AutorskyHonorar(Klasifikacia):
    def __init__(self, *args, **kwargs):
        self._meta.get_field('zdroj').default = 1       #111
        self._meta.get_field('program').default = 1     #Ostatné
        self._meta.get_field('zakazka').default = 1     #Beliana
        self._meta.get_field('ekoklas').default = 58    #633018	Licencie
        super(Klasifikacia, self).__init__(*args, **kwargs)

    cislo = models.CharField("Číslo platby", max_length=50)
    doslo_datum = models.DateField('Vyplatené dňa',
            blank=True, null=True)
    suma = models.DecimalField("Vyplatená suma", 
            help_text = "Zadajte honorár vyplatený autorom ako záporné číslo (stĺpec'Vyplatené spolu' z tabuľky Zmluvy / Vyplácanie aut. honorárov)",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    suma_lf = models.DecimalField("Odvedená suma Literárnemu fondu",
            help_text = "Zadajte sumu odvevenú Literárnemu fondu ako záporné číslo (stĺpec'Odvod LF' z tabuľky Zmluvy / Vyplácanie aut. honorárov)",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    suma_dan = models.DecimalField("Odvedená daň",
            help_text = "Zadajte daň odvevenú Finančnej správe záporné číslo (stĺpec 'Odvedená daň' z tabuľky Zmluvy / Vyplácanie aut. honorárov)",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Autorský honorár'
        verbose_name_plural = 'Autorské honoráre'
    def __str__(self):
        return f'Autorské honotáre {self.cislo}'

def system_file_path(instance, filename):
    return os.path.join(TMPLTS_DIR_NAME, filename)

class SystemovySubor(models.Model):
    subor_nazov =  models.CharField("Názov", max_length=100)
    subor_popis = models.CharField("Popis/účel", max_length=100)
    # opakované uploadovanie súboru vytvorí novú verziu
    #subor = models.FileField("Súbor",upload_to=TMPLTS_DIR_NAME, null = True, blank = True)
    # opakované uploadovanie súboru prepíše existujúci súbor (nevytvorí novú verziu)
    subor = models.FileField(storage=OverwriteStorage(), upload_to=system_file_path, null = True, blank = True)
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Systémový súbor'
        verbose_name_plural = 'Systémové súbory'
    def __str__(self):
        return(self.subor_nazov)
