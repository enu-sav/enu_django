from django.db import models
from django.core.exceptions import ValidationError

#záznam histórie
#https://django-simple-history.readthedocs.io/en/latest/admin.html
from simple_history.models import HistoricalRecords
from uctovnictvo.storage import OverwriteStorage
from polymorphic.models import PolymorphicModel

from beliana.settings import TMPLTS_DIR_NAME
import os,re, datetime
import numpy as np
from ipdb import set_trace as trace

class AnoNie(models.TextChoices):
    ANO = 'ano', 'Áno'
    NIE = 'nie', 'Nie'

class Mena(models.TextChoices):
    EUR = 'EUR'
    CZK = 'CZK'
    USD = 'USD'

class Poistovna(models.TextChoices):
    VSZP = 'VsZP', 'VšZP'
    DOVERA = "Dovera", 'Dôvera'
    UNION = "Union", 'Union'

class TypDochodku(models.TextChoices):
    STAROBNY = 'starobny', "starobný"
    INVALIDNY = 'invalidny', "invalidný"
    INVAL_VYSL = 'invalidny_vysl', "invalidný výsluhový"
    VYSLUHOVY = "vysluhovy",  "výsluhový po dovŕšení dôchodkového veku"
    PREDCASNY = "predcasny", "predčasný (poberateľovi zanikne nárok na výplatu predčasného dôchodku)"

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
        verbose_name_plural = 'Klasifikácia - Zdroje'

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
        verbose_name_plural = 'Klasifikácia - Programy'

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
        verbose_name_plural = 'Klasifikácia - Typy zákazky'

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
        verbose_name_plural = 'Klasifikácia - Ekonomická klasifikácia'
 

# Abstraktná trieda so všetkými spoločnými poľami, nepoužívaná samostatne
class PersonCommon(models.Model):
    # IBAN alebo aj kompletný popis s BIC a číslom účtu
    bankovy_kontakt = models.CharField("Bankový kontakt", 
            help_text = "Zadajte IBAN bankového účtu.",
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
        verbose_name_plural = 'Faktúry - Dodávatelia'
    def __str__(self):
        return self.nazov

#Polymorphic umožní, aby Objednavka a PrijataFaktura mohli použiť ObjednavkaZmluva ako ForeignKey
class ObjednavkaZmluva(PolymorphicModel):
    cislo = models.CharField("Číslo", 
            #help_text: definovaný vo forms
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
    oznacenie = "O"    #v čísle faktúry, Fa-2021-123
    # Polia
    objednane_polozky = models.TextField("Objednané položky", 
            help_text = "Po riadkoch zadajte položky s poľami oddelenými bodkočiarkou: Názov položky; merná jednotka (ks, kg, l, m, m2, m3,...); Množstvo; Cena za jednotku bez DPH",
            max_length=5000, null=True, blank=True)
    datum_vytvorenia = models.DateField('Dátum vytvorenia',
            help_text = "Zadajte dátum vytvorenia objednávky",
            default=datetime.datetime.now,
            blank=True, null=True)
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Objednávka'
        verbose_name_plural = 'Faktúry - Objednávky'
    def __str__(self):
        return f"{self.dodavatel}, objednávka, {self.cislo}"

class Rozhodnutie(ObjednavkaZmluva):
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Rozhodnutie'
        verbose_name_plural = 'Faktúry - Rozhodnutia'
    def __str__(self):
        return f"{self.dodavatel}, rozhodnutie, {self.cislo}"

class Zmluva(ObjednavkaZmluva):
    url_zmluvy = models.URLField('URL zmluvy', 
            help_text = "Zadajte URL pdf súboru zmluvy zo stránky CRZ.",
            null=True,
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
        verbose_name_plural = 'Faktúry - Zmluvy'
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
    poznamka = models.CharField("Poznámka", 
            max_length=200, 
            null=True,
            blank=True)
    class Meta:
        abstract = True

#https://stackoverflow.com/questions/55543232/how-to-upload-multiple-files-from-the-django-admin
#Vykoná sa len pri vkladaní suborov cez GUI. Pri programovom vytváraní treba cestu nastaviť
def platobny_prikaz_upload_location(instance, filename):
    return filename

class PrijataFaktura(Klasifikacia):
    oznacenie = "Fa"    #v čísle faktúry, Fa-2021-123
    # Polia
    cislo = models.CharField("Číslo faktúry", 
            #help_text: definovaný vo forms
            max_length=50)
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
        verbose_name_plural = 'Faktúry - Prijaté faktúry'
    def __str__(self):
        return f'Faktúra k "{self.objednavka_zmluva}" : {self.suma} €'

class AutorskyHonorar(Klasifikacia):
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

    # test platnosti dát
    def clean(self): 
        if self.suma >= 0 or self.suma_lf > 0 or self.suma_dan > 0:
            raise ValidationError("Položky 'Vyplatená suma' a 'Odvedená daň' musia byť záporné, položka 'Odvedená suma Literárnemu fondu' musí byť záporná alebo rovná 0")

    class Meta:
        verbose_name = 'Autorský honorár'
        verbose_name_plural = 'Autorské honoráre'
    def __str__(self):
        return f'Autorské honotáre {self.cislo}'

class PrispevokNaStravne(Klasifikacia):
    oznacenie = "PS"    #v čísle faktúry, FS-2021-123
    cislo = models.CharField("Číslo príspevku (za mesiac)", max_length=50)
    suma_zamestnavatel = models.DecimalField("Príspevok zamesnávateľa", 
            help_text = "Zadajte celkový príspevok zamestnávateľa (Ek. klas. 642014) ako zápornú hodnotu",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    # Položka suma_socfond nemá Ek. klasifikáciu, soc. fond nie sú peniaze EnÚ
    suma_socfond = models.DecimalField("Príspevok zo soc. fondu", 
            help_text = "Zadajte celkový príspevok zo sociálneho fondu ako zápornú hodnotu1",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    history = HistoricalRecords()

    # test platnosti dát
    def clean(self): 
        if self.suma_zamestnavatel >= 0 or self.suma_socfond > 0:
            raise ValidationError("Položky 'Príspevok zamestnávateľa' a 'Príspevok zo soc. fondu' musia byť záporné.")

    class Meta:
        verbose_name = 'Príspevok na stravné'
        verbose_name_plural = 'Príspevky na stravné'
    def __str__(self):
        return f'Príspevok na stravné {self.cislo}'

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


# fyzická osoba, najmä dohodári
class FyzickaOsoba(PersonCommon):
    email = models.EmailField("Email", max_length=200, null=True, blank=True)
    titul_pred_menom = models.CharField("Titul pred menom", max_length=100, null=True, blank=True) #optional
    meno = models.CharField("Meno", max_length=200)
    priezvisko = models.CharField("Priezvisko", max_length=200)
    titul_za_menom = models.CharField("Titul za menom", max_length=100, null=True, blank=True)     #optional
    rodne_cislo = models.CharField("Rodné číslo", max_length=20, null=True, blank=True) 
    poznamka = models.CharField("Poznámka", max_length=200, blank=True)

    class Meta:
        abstract = True
    def __str__(self):
        return self.rs_login

class Dohodar(FyzickaOsoba):
    datum_nar = models.DateField('Dátum narodenia', blank=True, null=True)
    rod_priezvisko = models.CharField("Rodné priezvisko", max_length=100, null=True, blank=True)
    miesto_nar = models.CharField("Miesto narodenia", max_length=100, null=True, blank=True)
    #stav = models.CharField("Stav", max_length=100, null=True, blank=True)
    poberatel_doch = models.CharField("Poberateľ dôchodku", 
            max_length=10, 
            null=True, 
            blank=True,
            choices=AnoNie.choices)
    typ_doch = models.CharField("Typ dôchodku", 
            max_length=100, 
            null=True, 
            blank=True,
            choices=TypDochodku.choices)
    poistovna = models.CharField("Zdravotná poisťovňa",
            max_length=20, 
            null=True, 
            blank=True,
            choices=Poistovna.choices)
    cop = models.CharField("Číslo OP", max_length=20, null=True, blank=True)
    # test platnosti dát
    def clean(self): 
        if self.poberatel_doch == AnoNie.ANO and not self.typ_doch:
            raise ValidationError("V prípade poberateľa dôchodku je potrebné určiť typ dôchodku")
    class Meta:
        verbose_name = "Dohodár"
        verbose_name_plural = "Dohody - Dohodári"
    def __str__(self):
        return f"{self.priezvisko}, {self.meno}"

#Polymorphic umožní, aby DoVP a PrijataFaktura mohli použiť ObjednavkaZmluva ako ForeignKey
class Dohoda(PolymorphicModel, Klasifikacia):
    cislo = models.CharField("Číslo", 
            #help_text: definovaný vo forms
            max_length=50)
    zmluvna_strana = models.ForeignKey(Dohodar,
            on_delete=models.PROTECT, 
            verbose_name = "Zmluvná strana",
            related_name='%(class)s_dohoda')  #zabezpečí rozlíšenie modelov DoVP a DoPC
    predmet = models.TextField("Pracovná činnosť", 
            help_text = "Zadajte stručný popis práce (max. 250 znakov, 3 riadky)",
            max_length=250,
            blank=True, null=True)
    datum_od = models.DateField('Dátum od',
            help_text = "Zadajte dátum začiatku platnosti dohody",
            blank=True, null=True)
    datum_do = models.DateField('Dátum do',
            help_text = "Zadajte dátum konca platnosti dohody",
            blank=True, null=True)
    class Meta:
        verbose_name = "Dohoda"
        verbose_name_plural = "Dohody"
        #abstract = True

class DoVP(Dohoda):
    oznacenie = "DoVP"
    odmena_celkom = models.DecimalField("Celková suma v EUR", 
            help_text = "Zadajte celkovú odmenu za vykonanú prácu. Bude vyplatená po odovzdaní práce a výkazu",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    hod_celkom = models.DecimalField("Predpokl. počet hodín",
            help_text = "Uveďte predpokladaný celkový počet odpracovaných hodín",
            max_digits=8, 
            decimal_places=1, 
            default=0)
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Dohoda o vykonaní práce'
        verbose_name_plural = 'Dohody - Dohody o vykonaní práce'
    def __str__(self):
        return f"{self.cislo}; {self.zmluvna_strana}"

class DoPC(Dohoda):
    oznacenie = "DoPC"
    odmena_hod = models.DecimalField("Odmena / hod",
            help_text = "Odmena za 1 hodinu práce. Vyplňte len ak ide o novú dohodu. Ak vkladáte údaje za už ukončenú dohodu, ponechajte hodnotu 0.",
            max_digits=8,
            decimal_places=2, 
            default=0)
    hod_tyzden = models.DecimalField("Hodín za týždeň",
            help_text = "Dohodnutý počet odpracovaných hodín za týždeň. Vyplňte len ak ide o novú dohodu. Ak vkladáte údaje za už ukončenú dohodu, ponechajte hodnotu 0.",
            max_digits=8, 
            decimal_places=1, 
            default=0)
    odmena_celkom = models.DecimalField("Celková odmena v EUR", 
            help_text = "Vyplňte, len ak vkladáte údaje za už ukončenú dohodu. Inak bude hodnota tohoto poľa vypočítaná z hodnoty ostatných polí.",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Dohoda o pracovnej činnosti'
        verbose_name_plural = 'Dohody - Dohody o pracovnej činnosti'
    # test platnosti dát
    def clean(self): 
        poc_dni = np.busday_count(
                self.datum_od,
                self.datum_do+datetime.timedelta(days=1),   #vrátane posledného dňa
                weekmask=[1,1,1,1,1,0,0])
        pocet_hodin = poc_dni * self.hod_tyzden/5
        if pocet_hodin > 350:
            raise ValidationError(f"Celkový počet {pocet_hodin} hodín za určené obdobie presahuje maximálny povolený počet 350. Znížte počet hodín za týždeň alebo skráťte obdobie.")

    def save(self, *args, **kwargs):
        if self.odmena_hod and self.hod_tyzden:
            poc_dni = np.busday_count(
                    self.datum_od,
                    self.datum_do+datetime.timedelta(days=1),   #vrátane posledného dňa
                    weekmask=[1,1,1,1,1,0,0])
            self.odmena_celkom = self.odmena_hod * poc_dni * self.hod_tyzden/5
        super(DoPC, self).save(*args, **kwargs)
    def __str__(self):
        return f"{self.cislo}; {self.zmluvna_strana}"

class VyplacanieDohod(models.Model):
    dohoda = models.ForeignKey(Dohoda, 
            null=True, 
            verbose_name = "Dohoda",
            on_delete=models.PROTECT, 
            related_name='vyplacanie')    
    vyplatena_odmena = models.DecimalField("Vyplatená odmena v EUR", 
            help_text = "Uveďte vyplatenú sumu",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    datum_vyplatenia = models.DateField('Dátum vyplatenia dohody',
            help_text = "Zadajte dátum vyplatenia dohody",
            default=datetime.datetime.now,
            blank=True, null=True)
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Vyplatenie dohody'
        verbose_name_plural = 'Dohody - Vyplácanie dohôd'

