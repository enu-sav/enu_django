from django.db import models
from django.core.exceptions import ValidationError

#záznam histórie
#https://django-simple-history.readthedocs.io/en/latest/admin.html
from simple_history.models import HistoricalRecords
from uctovnictvo.storage import OverwriteStorage
from .odvody import DohodarOdvodySpolu
from .rokydni import mesiace
from polymorphic.models import PolymorphicModel
from django.utils.safestring import mark_safe
from decimal import Decimal

from beliana.settings import TMPLTS_DIR_NAME, PLATOVE_VYMERY_DIR, DOHODY_DIR, PRIJATEFAKTURY_DIR, PLATOBNE_PRIKAZY_DIR
from beliana.settings import ODVODY_VYNIMKA, DAN_Z_PRIJMU
import os,re, datetime
import numpy as np
from ipdb import set_trace as trace

#acces label: AnoNie('ano').label
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
    history = HistoricalRecords()
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
    history = HistoricalRecords()
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
    history = HistoricalRecords()
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
    history = HistoricalRecords()
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
            max_length=200, null=True)
    adresa_ulica = models.CharField("Adresa – ulica a číslo domu", max_length=200, null=True, blank=True)
    adresa_mesto = models.CharField("Adresa – PSČ a mesto", max_length=200, null=True)
    adresa_stat = models.CharField("Adresa – štát", max_length=100, null=True)
    datum_aktualizacie = models.DateField('Dátum aktualizácie', null=True,auto_now=True)
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

# použité len pri vkladané cez admin formulár
def objednavka_upload_location(instance, filename):
    return os.path.join(OBJEDNAVKY_DIR, filename)
class Objednavka(ObjednavkaZmluva):
    oznacenie = "O"    #v čísle faktúry, Fa-2021-123
    # Polia
    objednane_polozky = models.TextField("Objednané položky", 
            help_text = mark_safe("<p>Po riadkoch zadajte objednávané položky:</p>\
                <ol>\
                <li>možnosť: so 4 poľami oddelenými bodkočiarkou v poradí: <b>názov položky</b>; <b>merná jednotka</b> - ks, kg, l, m, m2, m3; <b>množstvo</b>; <b>cena za jednotku bez DPH</b>, napr. <em>Euroobal A4;bal;10;7,50</em>. <br />Cena za jednotlivé položky a celková suma sa dopočíta. Pri výpočte sa berie do úvahy, či dodávateľ účtuje alebo neúčtuje cenu s DPH. </li>\
                <li>možnosť: ako jednoduchý text bez bodkočiarok, napr. <em>Objednávame tovar podľa priloženej ponuky.</em></li>\
                </ol>"),

            max_length=5000, null=True, blank=True)
    datum_vytvorenia = models.DateField('Dátum vytvorenia',
            help_text = "Zadajte dátum vytvorenia objednávky",
            default=datetime.datetime.now,
            blank=True, null=True)
    subor_objednavky = models.FileField("Súbor objednávky",
            help_text = "Súbor s objednávkou a krycím listom. Generuje sa akciou 'Vytvoriť objednávku'",
            upload_to=objednavka_upload_location,
            null = True, blank = True)
    termin_dodania = models.CharField("Termím dodania", 
            max_length=30, 
            help_text = "Určite termín dodania (dátum alebo slovné určenie)",
            null=True,
            blank=True)
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
    return os.path.join(PLATOBNE_PRIKAZY_DIR, filename)
def prijata_faktura_upload_location(instance, filename):
    return os.path.join(PRIJATEFAKTURY_DIR, filename)
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
    prijata_faktura = models.FileField("Faktúra dodádateľa",
            help_text = "Súbor s faktúrou od dodávateľa",
            upload_to=prijata_faktura_upload_location, 
            null = True, blank = True)
    platobny_prikaz = models.FileField("Platobný príkaz pre THS-ku",
            help_text = "Súbor s platobným príkazom a krycím listom pre THS-ku. Generuje sa akciou 'Vytvoriť platobný príkaz a krycí list pre THS'",
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
    subor_popis = models.TextField("Popis/účel", max_length=250)
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
    email = models.EmailField("Email", max_length=200, null=True)
    titul_pred_menom = models.CharField("Titul pred menom", max_length=100, null=True, blank=True) #optional
    meno = models.CharField("Meno", max_length=200)
    priezvisko = models.CharField("Priezvisko", max_length=200)
    titul_za_menom = models.CharField("Titul za menom", max_length=100, null=True, blank=True)     #optional
    rodne_cislo = models.CharField("Rodné číslo", max_length=20, null=True)
    poznamka = models.CharField("Poznámka", max_length=200, blank=True)

    class Meta:
        abstract = True
    def __str__(self):
        return self.rs_login

class ZamestnanecDohodar(PolymorphicModel, FyzickaOsoba):
    datum_nar = models.DateField('Dátum narodenia', null=True)
    rod_priezvisko = models.CharField("Rodné priezvisko", max_length=100, blank=True, null=True)
    miesto_nar = models.CharField("Miesto narodenia", max_length=100, null=True)
    st_prislusnost = models.CharField("Štátna príslušnosť", max_length=100, null=True)
    stav = models.CharField("Stav", max_length=100, null=True)
    poberatel_doch = models.CharField("Poberateľ dôchodku", 
            max_length=10, 
            null=True, 
            choices=AnoNie.choices)
    typ_doch = models.CharField("Typ dôchodku", 
            max_length=100, 
            null=True, 
            blank=True,
            choices=TypDochodku.choices)
    datum_doch = models.DateField('Dôchodca od',
            help_text = "Zadajte dátum vzniku dôchodku",
            blank=True,
            null=True)
    ztp = models.CharField("ZŤP",
            help_text = "Uveďte, či osoba je 'ZŤP'",
            max_length=10, 
            choices=AnoNie.choices)
    datum_ztp = models.DateField('ZŤP od',
            help_text = "Ak je osoba 'ZŤP, zadajte dátum vzniku ZŤP",
            blank=True,
            null=True)
    poistovna = models.CharField("Zdravotná poisťovňa",
            max_length=20, 
            null=True, 
            choices=Poistovna.choices)
    cop = models.CharField("Číslo OP", max_length=20, null=True)
    # test platnosti dát
    def clean(self): 
        if self.poberatel_doch == AnoNie.ANO and not self.typ_doch:
            raise ValidationError("V prípade poberateľa dôchodku je potrebné zadať typ dôchodku")
        if self.poberatel_doch == AnoNie.ANO and not self.datum_doch:
            raise ValidationError("V prípade poberateľa dôchodku je potrebné zadať dátum vzniku dôchodku")
        if self.ztp == AnoNie.ANO and not self.datum_ztp:
            raise ValidationError("V prípade ZŤP osoby je potrebné zadať dátum vzniku ZŤP")
    #class Meta:
        #verbose_name = "Zamestnanec / dohodár"
        #verbose_name_plural = "Zamestnanci / dohodári"
    def __str__(self):
        return f"{self.priezvisko}, {self.meno}"

class Zamestnanec(ZamestnanecDohodar):
    cislo_zamestnanca = models.CharField("Číslo zamestnanca", 
            null = True,
            max_length=50)
    zapocitane_roky = models.IntegerField("Započítané roky",
            help_text = "Započítané celé roky z predchádzajúcich zamestnaní",
            blank=True,
            null=True)
    zapocitane_dni = models.IntegerField("Započítané dni",
            help_text = "Započítané dni z predchádzajúcich zamestnaní.",
            blank=True,
            null=True)
    zamestnanie_od = models.DateField('Zamestnanie v EnÚ od',
            help_text = "Dátum nástupu do zamestnania v EnÚ.",
            blank=True,
            null=True)
    history = HistoricalRecords()
    class Meta:
        verbose_name = "Zamestnanec"
        verbose_name_plural = "Zamestnanci"
    def __str__(self):
        return f"Z {self.priezvisko}, {self.meno}"

class Dohodar(ZamestnanecDohodar):
    history = HistoricalRecords()
    class Meta:
        verbose_name = "Dohodár"
        verbose_name_plural = "Dohodári"
    def __str__(self):
        return f"D {self.priezvisko}, {self.meno}"

def vymer_file_path(instance, filename):
    return os.path.join(PLATOVE_VYMERY_DIR, filename)

#Polymorphic umožní, aby DoVP a PrijataFaktura mohli použiť ObjednavkaZmluva ako ForeignKey
class PlatovyVymer(Klasifikacia):
    cislo_zamestnanca = models.CharField("Číslo zamestnanca", 
            null = True,
            max_length=50)
    zamestnanec = models.ForeignKey(Zamestnanec,
            on_delete=models.PROTECT, 
            verbose_name = "Zamestnanec",
            related_name='%(class)s_zamestnanec')  #zabezpečí rozlíšenie modelov, keby dačo
    suborvymer = models.FileField("Výmer",
            help_text = "Vložte zoskenovaný platový výmer (vytvorený mzdovou účtárňou)",
            storage=OverwriteStorage(), 
            upload_to=vymer_file_path, 
            null = True, 
            blank = True 
            )
    datum_od = models.DateField('Dátum od',
            help_text = "Zadajte dátum začiatku platnosti výmeru",
            null=True)
    datum_do = models.DateField('Dátum do',
            help_text = "Nechajte prázdne alebo zadajte dátum ukončenia prac. pomeru. Ak sa pre zamestnanca vytvorí nový výmer, toto pole v predchádzajúcom výmere sa vyplní automaticky, čím sa jeho platnosť ukončí",
            blank=True,
            null=True)
    tarifny_plat = models.DecimalField("Tarifný plat", 
            help_text = "Tarifný plat podľa prílohy č. 5 zákona",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    osobny_priplatok = models.DecimalField("Osobný príplatok", 
            help_text = "Osobný príplatok podľa § 10 zákona",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    funkcny_priplatok = models.DecimalField("Funkčný príplatok", 
            max_digits=8, 
            decimal_places=2, 
            default=0)
    platova_trieda = models.IntegerField("Platová trieda",
            null=True)
    platovy_stupen = models.IntegerField("Platový stupeň",
            null=True)
    uvazok = models.DecimalField("Úväzok (hod/týždeň)", 
            help_text = "Zadajte pracovný úväzok týždenne (najviac 37,5 hod)",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    praxroky = models.IntegerField("Prax (roky)",
            help_text = "Pole sa vyplňuje automaticky. Ak je pole 'Dátum do' prázdne, tak toto pole obsahuje počet celých rokov praxe do začiatku platnosti tohoto výmeru. Ak je pole 'Dátum do' vyplnené, tak toto pole obsahuje počet celých rokov praxe do konca platnosti tohoto výmeru.",
            blank=True,
            null=True)
    praxdni = models.IntegerField("Prax (dni)",
            help_text = "Pole sa vyplňuje automaticky. Ak je pole 'Dátum do' prázdne, tak toto pole obsahuje počet dní praxe neúplného posledného roku do začiatku platnosti tohoto výmeru. Ak je pole 'Dátum do' vyplnené, tak toto pole obsahuje počet dní praxe do konca platnosti tohoto výmeru.",
            blank=True,
            null=True)
    zamestnanieroky = models.IntegerField("Doba zamestnania v Enú (roky)",
            help_text = "Pole sa vyplňuje automaticky, ak je pole 'Dátum do' vyplnené. Vtedy toto pole obsahuje počet celých rokov zamestnania v EnÚ do konca platnosti tohoto výmeru",
            blank=True,
            null=True)
    zamestnaniedni = models.IntegerField("Doba zamestnania v EnÚ (dni)",
            help_text = "Pole sa vyplňuje automaticky, ak je pole 'Dátum do' vyplnené. Vtedy toto pole obsahuje počet dní zamestnania neúplného posledného roku do konca platnosti tohoto výmeru.",
            blank=True,
            null=True)
    datum_postup = models.DateField('Dátum pl. postupu',
            help_text = "Dátum najbližšieho platového postupu. Pole sa vyplňuje automaticky, ak nie je pole 'Dátum do' vyplnené, inak je prázdne",
            blank=True,
            null=True)
    history = HistoricalRecords()
    class Meta:
        verbose_name = "Platový výmer"
        verbose_name_plural = "Platové výmery"
    def __str__(self):
        od = self.datum_od.strftime('%d. %m. %Y') if self.datum_od else '--'
        return f"{self.zamestnanec.priezvisko}, {od}"

# použité len pri vkladané cez admin formulár
def dohoda_upload_location(instance, filename):
    return os.path.join(DOHODY_DIR, filename)
#Polymorphic umožní, aby DoVP a PrijataFaktura mohli použiť ObjednavkaZmluva ako ForeignKey
class Dohoda(PolymorphicModel, Klasifikacia):
    cislo = models.CharField("Číslo", 
            #help_text: definovaný vo forms
            max_length=50)
    zmluvna_strana = models.ForeignKey(ZamestnanecDohodar,
            on_delete=models.PROTECT, 
            verbose_name = "Zmluvná strana",
            related_name='%(class)s_dohoda')  #zabezpečí rozlíšenie modelov DoVP a DoPC
    vynimka = models.CharField("Uplatnená výnimka", 
            max_length=3, 
            help_text = "Uveďte 'Áno', ak si dohodár na túto dohodu uplatňuje odvodovú výnimku",
            null = True,
            choices=AnoNie.choices)
    predmet = models.TextField("Pracovná činnosť", 
            help_text = "Zadajte stručný popis práce (max. 250 znakov, 3 riadky)",
            max_length=500,
            null=True)
    datum_od = models.DateField('Dátum od',
            help_text = "Zadajte dátum začiatku platnosti dohody",
            null=True)
    datum_do = models.DateField('Dátum do',
            help_text = "Zadajte dátum konca platnosti dohody",
            null=True)
    #Vypĺňa sa pri vytvorení vyplácania, pri opakovanej platbe obsahuje dátum za každú platbu
    vyplatene = models.CharField("Vyplatené", 
            help_text = "Dátum odoslania podkladov na vyplatenie, vypĺňa sa automaticky",
            null = True, blank = True,
            max_length=200)
    class Meta:
        verbose_name = "Dohoda"
        verbose_name_plural = "Dohody"
        #abstract = True
    subor_dohody = models.FileField("Súbor dohody",
            help_text = "Súbor s textom dohody. Generuje sa akciou 'Vytvoriť subor dohody'",
            upload_to=dohoda_upload_location, 
            null = True, blank = True)

class DoVP(Dohoda):
    oznacenie = "DoVP"
    odmena_celkom = models.DecimalField("Celková suma v EUR", 
            help_text = "Zadajte celkovú odmenu za vykonanú prácu. Bude vyplatená po odovzdaní práce a výkazu",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    hod_celkom = models.DecimalField("Predpokl. počet hodín",
            help_text = "Uveďte predpokladaný celkový počet odpracovaných hodín, najviac 350.",
            max_digits=8, 
            decimal_places=1, 
            default=0)
    id_tsh = models.CharField("Číslo pridadené THS",
            help_text = "Uveďte číslo, pod ktorým dohody vedie THS",
            null = True, blank = True,
            max_length=100)
    pomocnik = models.CharField("Pomoc rod. príslušníkov", 
            help_text = "Uveďte zoznam rod. príslušníkov, ktorí budú pomáhať pri vykonávaní činnosti, alebo nechajte prázdne. Pre každého uveďte meno a priezvisko.",
            null = True, blank = True,
            max_length=100)
    history = HistoricalRecords()
    # test platnosti dát
    def clean(self): 
        num_days = (self.datum_do - self.datum_od).days
        if num_days > 366:
            raise ValidationError(f"Doba platnosti dohody presahuje maximálnu povolenú dobu 12 mesiacov.")
        if self.hod_celkom > 350:
            raise ValidationError(f"Celkový počet {pocet_hodin} hodín maximálny zákonom povolený povolený počet 350.")

    class Meta:
        verbose_name = 'Dohoda o vykonaní práce'
        verbose_name_plural = 'Dohody - Dohody o vykonaní práce'
    def __str__(self):
        return f"{self.zmluvna_strana}; {self.cislo}"

class DoBPS(Dohoda):
    oznacenie = "DoBPS"
    odmena_celkom = models.DecimalField("Celková suma v EUR", 
            help_text = "Zadajte celkovú odmenu za vykonanú prácu. Bude vyplatená po odovzdaní práce a výkazu",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    hod_mesacne = models.DecimalField("Predpokl. počet hodín mesačne",
            help_text = "Uveďte predpokladaný priemerný počet odpracovaných hodín. Počet nesmie v priemere prekračovať 80 hodín mesačne",
            max_digits=8, 
            decimal_places=1, 
            default=0)
    datum_ukoncenia = models.DateField('Dátum ukončenia',
            help_text = "Zadajte dátum predčasného ukončenia platnosti dohody",
            blank = True,
            null=True)
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Dohoda o bigádnickej práci študentov'
        verbose_name_plural = 'Dohody - Dohody o bigádnickej práci študentov'
    def __str__(self):
        return f"{self.zmluvna_strana}; {self.cislo}"

class DoPC(Dohoda):
    oznacenie = "DoPC"
    odmena_mesacne = models.DecimalField("Odmena za mesiac",
            help_text = "Dohodnutá mesačná odmena",
            max_digits=8,
            decimal_places=2, 
            default=0)
    hod_mesacne = models.DecimalField("Hodín za mesiac",
            help_text = "Dohodnutý počet odpracovaných hodín za mesiac, najviac 40",
            max_digits=8, 
            decimal_places=1, 
            default=0)
    datum_ukoncenia = models.DateField('Dátum ukončenia',
            help_text = "Zadajte dátum predčasného ukončenia platnosti dohody",
            blank = True,
            null=True)
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Dohoda o pracovnej činnosti'
        verbose_name_plural = 'Dohody - Dohody o pracovnej činnosti'
    # test platnosti dát
    def clean(self): 
        if self.hod_mesacne > 40:
            raise ValidationError(f"Počet hodín mesačne {hod_mesacne} presahuje maximálny zákonom povolený počet 40.")
    def __str__(self):
        return f"{self.zmluvna_strana}; {self.cislo}"

class VyplacanieDohod(models.Model):
    dohoda = models.ForeignKey(Dohoda, 
            verbose_name = "Dohoda",
            on_delete=models.PROTECT,
            null = True,
            related_name='vyplacanie')
    vyplatena_odmena = models.DecimalField("Vyplatená odmena",
            help_text = "Zadajte sumu na vyplatenie. Ak ponecháte 0, doplní sa dohodnutá suma z dohody",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    datum_vyplatenia = models.DateField('Dátum odoslania podkladov dohody',
            help_text = "Zadajte dátum odoslania podkladov na vyplatenie dohody. Ostatné polia sa vyplnia automaticky.",
            null=True)
    #odvody a platby
    poistne_zamestnavatel = models.DecimalField("Odvody zamestnávateľ",
            help_text = "Odvody zamestnávateľa (sociálne a zdravotné)",
            max_digits=8,
            decimal_places=2, 
            default=0)
    poistne_dohodar = models.DecimalField("Odvody dohodár",
            help_text = "Odvody uhradené za dohodára (sociálne a zdravotné)",
            max_digits=8,
            decimal_places=2, 
            default=0)
    dan_dohodar = models.DecimalField("Daň dohodár",
            help_text = "Daň z príjmu uhradená za dohodára",
            max_digits=8,
            decimal_places=2, 
            default=0)
    na_ucet = models.DecimalField("Suma na účet",
            help_text = "Odmena odoslaná dohodárovi na účet",
            max_digits=8,
            decimal_places=2, 
            default=0)
    history = HistoricalRecords()
    def __str__(self):
        return f"Vyplatenie dohody {self.dohoda}"

    def clean(self): 
        #súbor s údajmi o odvodoch
        if not self.dohoda:
            raise ValidationError(f"Pole '{VyplacanieDohod._meta.get_field('dohoda').verbose_name}' nemôže byť prázdne")
        if not self.datum_vyplatenia:
            raise ValidationError(f"Pole '{VyplacanieDohod._meta.get_field('datum_vyplatenia').verbose_name}' nemôže byť prázdne")

        nazov_objektu = "Odvody zamestnancov a dohodárov"  #Presne takto musí byť objekt pomenovaný
        objekt = SystemovySubor.objects.filter(subor_nazov = nazov_objektu)
        if not objekt:
            return f"V systéme nie je definovaný súbor '{nazov_objektu}'."
        nazov_suboru = objekt[0].subor.file.name 
        # prebrať sumu z dohody
        #if self.dohoda and not self.vyplatena_odmena:
        vyplatena = VyplacanieDohod.objects.filter(dohoda = self.dohoda)
        if self.dohoda:
            if type(self.dohoda) == DoVP:
                #Overiť, či už dohoda nebola zaznamenana - len DoVP
                if vyplatena:
                    raise ValidationError(f"Dohoda '{self.dohoda}' už bola vyplatená ({vyplatena[0].datum_vyplatenia}).")
                # Ak je odmena rovná 0, prebrať sumu z dohody
                if not self.vyplatena_odmena:
                    self.vyplatena_odmena = self.dohoda.odmena_celkom
                td = "DoVP"
            elif type(self.dohoda) == DoPC:
                if vyplatena:
                    if self.datum_vyplatenia.month == vyplatena[0].datum_vyplatenia.month:
                        raise ValidationError(f"Dohoda '{self.dohoda}' už bola za mesiac {mesiace[self.datum_vyplatenia.month-1]} vyplatená ({vyplatena[0].datum_vyplatenia}).")
                # Ak je odmena rovná 0, prebrať sumu z dohody
                if not self.vyplatena_odmena:
                    self.vyplatena_odmena = self.dohoda.odmena_mesacne 
                td = "DoPC"
        elif type(self.dohoda) == DoBPS:
            if vyplatena:
                if self.datum_vyplatenia.month == vyplatena[0].datum_vyplatenia.month:
                    raise ValidationError(f"Dohoda '{self.dohoda}' už bola za mesiac {mesiace[self.datum_vyplatenia.month-1]} vyplatená ({vyplatena[0].datum_vyplatenia}).")
            # Ak je odmena rovná 0, prebrať sumu z dohody
            if not self.vyplatena_odmena:
                self.vyplatena_odmena = self.dohoda.odmena_celkom
            td = "DoBPS"

        #Vynimka: v pripadade DoVP treba vyňatú sumu prispôsobiť dĺžke trvanie zmluvy
        if self.dohoda.vynimka and td in ["DoPC", "DoBPSForm"]:
            vynimka_suma = ODVODY_VYNIMKA    #vyplacané mesačne, fixná suma vynimky
        elif self.dohoda.vynimka and td in ["DoVP"]:
            pocet_mesiacov = 12*(self.dohoda.datum_do-self.dohoda.datum_od).days/365
            vynimka_suma = ODVODY_VYNIMKA * 12*(self.dohoda.datum_do-self.dohoda.datum_od).days/365
            pass
        else:
            vynimka_suma = 0    #bez výnimky

        #dochodok (musí byť umiestnené ZA vypočtom vynimka_suma
        if self.dohoda.zmluvna_strana.typ_doch in [TypDochodku.STAROBNY, TypDochodku.PREDCASNY, TypDochodku.VYSLUHOVY]:
            td = "StarDoch"
        elif self.dohoda.zmluvna_strana.typ_doch in [TypDochodku.INVALIDNY, TypDochodku.INVAL_VYSL]:
            td = "InvDoch"

        vyplatena_odmena = float(self.vyplatena_odmena)
        odvody_zam, odvody_prac = DohodarOdvodySpolu(nazov_suboru, vyplatena_odmena, td, vynimka_suma) 
        self.poistne_zamestnavatel = odvody_zam
        self.poistne_dohodar = odvody_prac
        self.dan_dohodar = (vyplatena_odmena - self.poistne_dohodar) * DAN_Z_PRIJMU / 100
        self.na_ucet = vyplatena_odmena - self.poistne_dohodar - self.dan_dohodar

        #uložiť dátum vyplatenia do dohody. V prípade opakovaného vyplácania DoPC a DoBPS sa pridáva ďalší dátum do zoznamu
        vypl = "%s, "%self.dohoda.vyplatene if self.dohoda.vyplatene else ""
        self.dohoda.vyplatene=f"{vypl}{self.datum_vyplatenia}"
        self.dohoda.save()
        pass

    class Meta:
        verbose_name = 'Vyplatenie dohody'
        verbose_name_plural = 'Dohody - Vyplácanie dohôd'

