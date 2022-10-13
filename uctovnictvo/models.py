from django.db import models

from django.core.exceptions import ValidationError

#záznam histórie
#https://django-simple-history.readthedocs.io/en/latest/admin.html
from simple_history.models import HistoricalRecords
from uctovnictvo.storage import OverwriteStorage
from .odvody import DohodarOdvodySpolu, ZamestnanecOdvodySpolu, ZamestnanecOdvody, DohodarOdvody
from .rokydni import mesiace, koef_neodprac_dni, prekryv_dni, prac_dni
from polymorphic.models import PolymorphicModel
from django.utils.safestring import mark_safe
from decimal import Decimal

from beliana.settings import TMPLTS_DIR_NAME, PLATOVE_VYMERY_DIR, DOHODY_DIR, PRIJATEFAKTURY_DIR, PLATOBNE_PRIKAZY_DIR
from beliana.settings import ODVODY_VYNIMKA, DAN_Z_PRIJMU, OBJEDNAVKY_DIR, STRAVNE_DIR, REKREACIA_DIR
from beliana.settings import PN1, PN2, BEZ_PRIKAZU_DIR, DDS_PRISPEVOK
import os,re
from datetime import timedelta, date, datetime
from dateutil.relativedelta import relativedelta
import numpy as np
from ipdb import set_trace as trace

#access label: AnoNie('ano').label
class OdmenaAleboOprava(models.TextChoices):
    ODMENA = 'odmena', 'Odmena'
    OPRAVATARIF = 'opravatarif', 'Oprava tarifný plat'
    OPRAVAOSOB = 'opravaosob', 'Oprava osobný pr.'
    OPRAVARIAD = 'opravariad', 'Oprava pr. za riadenie'

#access label: AnoNie('ano').label
class AnoNie(models.TextChoices):
    ANO = 'ano', 'Áno'
    NIE = 'nie', 'Nie'

class Mena(models.TextChoices):
    EUR = 'EUR'
    CZK = 'CZK'
    USD = 'USD'
    GBP = 'GBP'

# Pre triedu classname určí číslo nasledujúceho záznamu v pvare X-2021-NNN
def nasledujuce_cislo(classname):
        # zoznam faktúr s číslom "PS-2021-123" zoradený vzostupne
        ozn_rok = f"{classname.oznacenie}-{datetime.now().year}-"
        itemlist = classname.objects.filter(cislo__istartswith=ozn_rok).order_by("cislo")
        if itemlist:
            latest = itemlist.last().cislo
            nove_cislo = int(re.findall(f"{ozn_rok}([0-9]+)",latest)[0]) + 1
            return "%s%03d"%(ozn_rok, nove_cislo)
        else:
            #sme v novom roku alebo trieda este nema instanciu
            return f"{ozn_rok}001"

# nasledujúce číslo Výdavkového pokladničného dokladu
def nasledujuce_VPD():
        # zoznam VPD zoradený podľa cislo_VPD vzostupne
        ozn_rok = f"{Pokladna.oznacenie}-{datetime.now().year}-"
        qs = Pokladna.objects.filter(cislo__istartswith=ozn_rok)
        itemlist=qs.exclude(cislo_VPD__isnull=True).order_by("cislo_VPD")
        return itemlist.last().cislo_VPD+1 if itemlist else 1

#ak sa doplni stav pred 'PODPISANA_ENU', treba doplniť test vo funkcii vytvorit_subory_zmluvy
class StavDohody(models.TextChoices):
    NOVA = "nova", "Nová"                        #Stav dohody po vytvorení
    VYTVORENA = "vytvorena", "Vytvorená"                        #Stav dohody po vytvorení súboru. Treba dať na podpis
    #PODPISANA_ENU = "podpisana_enu", "Podpísaná EnÚ"
    NAPODPIS = "napodpis", "Daná na podpis vedeniu EnÚ"
    ODOSLANA_DOHODAROVI = "odoslana_dohodarovi", "Daná dohodárovi na podpis"
    PODPISANA_DOHODAROM = "podpisana_dohodarom", "Podpísaná"
    DOKONCENA = "dokoncena", "Dokončená"

class TypNepritomnosti(models.TextChoices):
    MATERSKA = "materská", "Materská"   #Náhrada mzdy - prekážky osobné
    OCR = "ocr", "OČR"  #NP
    PN = "pn", "PN" #Náhrada mzdy - prekážky osobné
    DOVOLENKA = "dovolenka", "Dovolenka"    #Náhrada mzdy - dovolenka
    DOVOLENKA2 = "dovolenka2", "Poldeň dovolenky"
    LEKAR = "lekar", "Návšteva u lekára (L)"    #Náhrada mzdy - prekážky osobné
    LEKARDOPROVOD = "lekardoprovod", "Doprovod k lekárovi (L/D)"  #Náhrada mzdy - prekážky osobné
    PZV = "pzv", "Pracovné voľno (PzV, PV, P, S)"    #Náhrada mzdy - prekážky osobné
    NEPLATENE = "neplatene", "Neplatené voľno"

#access label: AnoNie('ano').label
class TypPokladna(models.TextChoices):
    DOTACIA = 'prijem_do_pokladne', 'Príjem do pokladne'
    VPD = 'vystavenie_vpd', 'Vystavenie VPD'

class Poistovna(models.TextChoices):
    VSZP = 'VsZP', 'VšZP'
    DOVERA = "Dovera", 'Dôvera'
    UNION = "Union", 'Union'

class Mesiace(models.TextChoices):
    JANUAR = "januar", "január"
    FEBRUAR = "februar", "február"
    MAREC = "marec", "marec"
    APRIL = "april", "apríl"
    MAJ = "maj", "máj"
    JUN = "jun", "jún"
    JUL = "jul", "júl"
    AUGUST = "august", "august"
    SEPTEMBER = "september", "september"
    OKTOBER = "oktober", "október"
    NOVEMBER = "november", "november"
    DECEMBER = "december", "december"

class TypDochodku(models.TextChoices):
    STAROBNY = 'starobny', "starobný"
    INVALIDNY = 'invalidny', "invalidný (len dohodári)"
    INVALIDNY30 = 'invalidny30', "invalidný 30 % (len zamestnanci)"
    INVALIDNY70 = 'invalidny70', "invalidný 70 % (len zamestnanci)"
    INVAL_VYSL = 'invalidny_vysl', "invalidný výsluhový"
    VYSLUHOVY = "vysluhovy",  "výsluhový po dovŕšení dôchodkového veku"
    PREDCASNY = "predcasny", "predčasný (poberateľovi zanikne nárok na výplatu predčasného dôchodku)"

#typ pravidelnej platby
class TypPP(models.TextChoices):
    ZALOHA_EL_ENERGIA = 'zaloha_el_energia', 'Záloha za el. energiu'

#typ platby nájomníka
class TypPN(models.TextChoices):
    NAJOMNE = 'najomne', 'Nájomné'
    SLUZBY = 'sluzby', 'Služby spojené s prenájmom'
    VYUCTOVANIE = 'vyuctovanie', 'Vyúčtovanie služieb'

class Zdroj(models.Model):
    kod = models.CharField("Kód", 
            help_text = "Zadajte kód zdroja - napr. 111, 46 alebo 42", 
            max_length=20)
    popis = models.CharField("Popis", 
            help_text = "Popíšte zdroj",
            null = True,
            blank = True,
            max_length=100)
    history = HistoricalRecords()
    def __str__(self):
        return f"{self.kod} - {self.popis}" if self.popis else self.kod
    class Meta:
        verbose_name = 'Zdroj'
        verbose_name_plural = 'Klasifikácia - Zdroje'

#V 2020 sa programy nepoužívajú, dohodnuté je použivať default=4 (nealokovaný)
class Program(models.Model):
    kod = models.CharField("Kód", 
            help_text = "Zadajte kód programu - napr. 087060J, 0EK1102 alebo 0EK1103",
            max_length=20)
    popis = models.CharField("Popis", 
            help_text = "Popíšte program",
            null = True,
            blank = True,
            max_length=100)
    history = HistoricalRecords()
    def __str__(self):
        return f"{self.kod} - {self.popis}" if self.popis else self.kod
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
        return f"{self.kod}"
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
        return f"{self.kod} - {' '.join(self.nazov.split(' ')[:4])}"
    class Meta:
        verbose_name = 'Ekonomická klasifikácia'
        verbose_name_plural = 'Klasifikácia - Ekonomická klasifikácia'

class Cinnost(models.Model):
    kod = models.CharField("Kód",
            help_text = "Zadajte kód činnosti",
            max_length=10)
    nazov = models.CharField("Názov",
            help_text = "Zadajte názov činosti",
            max_length=100)
    history = HistoricalRecords()
    def __str__(self):
        return f"{self.kod} - {' '.join(self.nazov.split(' ')[:4])}"
    class Meta:
        verbose_name = 'Činnosť'
        verbose_name_plural = 'Klasifikácia - Činnosť'

# Abstraktná trieda so všetkými spoločnými poľami, nepoužívaná samostatne
class PersonCommon(models.Model):
    # IBAN alebo aj kompletný popis s BIC a číslom účtu
    bankovy_kontakt = models.CharField("Bankový kontakt", 
            help_text = "Zadajte IBAN bankového účtu.",
            max_length=200, 
            blank=True,
            null=True)
    adresa_ulica = models.CharField("Adresa – ulica a číslo domu", max_length=200, null=True, blank=True)
    adresa_mesto = models.CharField("Adresa – PSČ a mesto", max_length=200, null=True)
    adresa_stat = models.CharField("Adresa – štát", max_length=100, null=True)
    datum_aktualizacie = models.DateField('Dátum aktualizácie', null=True,auto_now=True)
    class Meta:
        abstract = True

class InternyPartner(PersonCommon):
    nazov = models.CharField("Názov", max_length=200)
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Interný partner'
        verbose_name_plural = 'Faktúry - Interní partneri'
    def __str__(self):
        return self.nazov

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
                <li>možnosť: ako jednoduchý text bez bodkočiarok, napr. <em>Objednávame tovar podľa priloženej ponuky / priloženého zoznamu</em> (súbor takejto ponuky alebo zoznamu vložte do poľa <em>Súbor prílohy</em>).</li>\
                </ol>"),

            max_length=5000, null=True, blank=True)
    datum_vytvorenia = models.DateField('Dátum vytvorenia',
            help_text = "Zadajte dátum vytvorenia objednávky",
            default=datetime.now,
            blank=True, null=True)
    subor_objednavky = models.FileField("Súbor objednávky",
            help_text = "Súbor s objednávkou a krycím listom. Generuje sa akciou 'Vytvoriť objednávku'",
            upload_to=objednavka_upload_location,
            null = True, blank = True)
    subor_prilohy = models.FileField("Súbor prílohy",
            help_text = "Súbor s prílohou k objednávke. Použite, ak sa v poli <em>Objednané položky</em> takáto príloha spomína.", 
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
        verbose_name = 'Rozhodnutie / Povolenie'
        verbose_name_plural = 'Faktúry - Rozhodnutia a povolenia'
    def __str__(self):
        return f"{self.dodavatel} - Ro/Po - {self.cislo}"

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
            default = 4,    #'nealokovaný'
            related_name='%(class)s_klasifikacia')
    zakazka = models.ForeignKey(TypZakazky,
            on_delete=models.PROTECT,
            verbose_name = "Typ zákazky",
            related_name='%(class)s_klasifikacia')
    ekoklas = models.ForeignKey(EkonomickaKlasifikacia,
            on_delete=models.PROTECT,
            verbose_name = "Ekonomická klasifikácia",
            related_name='%(class)s_klasifikacia')
    cinnost = models.ForeignKey(Cinnost,
            on_delete=models.PROTECT,
            verbose_name = "Činnosť",
            default = 2,    #Činnosť 1a
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
class Platba(Klasifikacia):
    # Polia
    cislo = models.CharField("Číslo", 
            #help_text: definovaný vo forms
            max_length=50)
    dane_na_uhradu = models.DateField('Dané na úhradu dňa',
            help_text = 'Zadajte dátum odovzdania podpísaného platobného príkazu a krycieho listu na sekretariát na odoslanie THS. <br />Vytvorí sa záznam v <a href="/admin/dennik/dokument/">denníku prijatej a odoslanej pošty</a>.',
            blank=True, null=True)
    splatnost_datum = models.DateField('Dátum splatnosti',
            null=True)
    suma = models.DecimalField("Suma", 
            max_digits=8, 
            decimal_places=2, 
            null=True)
    platobny_prikaz = models.FileField("Platobný príkaz pre THS-ku",
            help_text = "Súbor s platobným príkazom a krycím listom pre THS-ku. Generuje sa akciou 'Vytvoriť platobný príkaz a krycí list pre THS'",
            upload_to=platobny_prikaz_upload_location, 
            null = True, blank = True)
    class Meta:
        abstract = True

class FakturaPravidelnaPlatba(Platba):
    objednavka_zmluva = models.ForeignKey(ObjednavkaZmluva, 
            null=True, 
            verbose_name = "Objednávka / zmluva",
            on_delete=models.PROTECT, 
            related_name='%(class)s_faktury')    

    # Koho uviesť ako adresata v denniku
    def adresat(self):
        return self.objednavka_zmluva.dodavatel.nazov if self.objednavka_zmluva else ""

    class Meta:
        abstract = True

class InternyPrevod(Platba):
    oznacenie = "IP"    #v čísle faktúry, IP-2021-123
    partner = models.ForeignKey(InternyPartner,
            on_delete=models.PROTECT, 
            verbose_name = "InternyPartner",
            null = True,
            related_name='%(class)s_requests_created')  #zabezpečí rozlíšenie modelov Objednavka a PrijataFaktura 
    doslo_datum = models.DateField('Došlo dňa',
            null=True)
    predmet = models.CharField("Predmet", 
            null = True,
            max_length=100)
    na_zaklade = models.CharField("Na základe", 
            null = True,
            max_length=100)
    history = HistoricalRecords()

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        if not self.doslo_datum: return []
        if self.doslo_datum <zden: return []
        kdatum =  date(zden.year, zden.month+1, zden.day) if zden.month+1 <= 12 else  date(zden.year+1, 1, 1)
        if self.doslo_datum >= kdatum: return []
        platba = {
                "nazov":f"Interný prevod",
                "suma": self.suma,
                "datum": self.doslo_datum,
                "cislo": self.cislo,
                "subjekt": self.partner.nazov,
                "zdroj": self.zdroj,
                "zakazka": self.zakazka,
                "ekoklas": self.ekoklas
                }
        return [platba]
    class Meta:
        verbose_name = "Interný prevod",
        verbose_name_plural = "Faktúry - Interné prevody"
    def __str__(self):
        return self.cislo

def prijata_faktura_upload_location(instance, filename):
    return os.path.join(PRIJATEFAKTURY_DIR, filename)
class PrijataFaktura(FakturaPravidelnaPlatba):
    oznacenie = "Fa"    #v čísle faktúry, Fa-2021-123
    # Polia
    dcislo = models.CharField("Dodávateľské číslo faktúry", 
            blank=True, 
            null=True,
            max_length=50)
    predmet = models.CharField("Predmet", 
            max_length=100)
    doslo_datum = models.DateField('Došlo dňa',
            null=True)
    mena = models.CharField("Mena", 
            max_length=3, 
            default= Mena.EUR,
            choices=Mena.choices)
    prijata_faktura = models.FileField("Faktúra dodádateľa",
            help_text = "Súbor s faktúrou od dodávateľa",
            upload_to=prijata_faktura_upload_location, 
            blank = True,
            null = True)
    history = HistoricalRecords()

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        if not self.dane_na_uhradu: return []
        if self.dane_na_uhradu <zden: return []
        kdatum =  date(zden.year, zden.month+1, zden.day) if zden.month+1 <= 12 else  date(zden.year+1, 1, 1)
        if self.dane_na_uhradu >= kdatum: return []
        typ = "zmluva" if type(self.objednavka_zmluva) == Zmluva else "objednávka" if type(self.objednavka_zmluva) == Objednavka else "rozhodnutie" 
        platba = {
                "nazov":f"Faktúra {typ}",
                "suma": self.suma,
                "datum": self.dane_na_uhradu,
                "cislo": self.cislo,
                "subjekt": self.adresat(),
                "zdroj": self.zdroj,
                "zakazka": self.zakazka,
                "ekoklas": self.ekoklas
                }
        return [platba]
    class Meta:
        verbose_name = 'Prijatá faktúra'
        verbose_name_plural = 'Faktúry - Prijaté faktúry'
    def __str__(self):
        return f'Faktúra k "{self.objednavka_zmluva}" : {self.suma} €'

class PravidelnaPlatba(FakturaPravidelnaPlatba):
    oznacenie = "PP"    #v čísle faktúry, Fa-2021-123
    # Polia
    history = HistoricalRecords()
    typ = models.CharField("Typ platby", 
            max_length=25, 
            choices=TypPP.choices)

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        if self.splatnost_datum <zden: return []
        kdatum =  date(zden.year, zden.month+1, zden.day) if zden.month+1 <= 12 else  date(zden.year+1, 1, 1)
        if self.splatnost_datum >= kdatum: return []
        nazov = "Faktúra záloha" if self.typ == TypPP.ZALOHA_EL_ENERGIA else ""
        platba = {
                "nazov":nazov,
                "suma": self.suma,
                "datum": self.dane_na_uhradu,
                "subjekt": f"{self.adresat()}, (za {zden.year}/{zden.month})", 
                "cislo": self.cislo,
                "zdroj": self.zdroj,
                "zakazka": self.zakazka,
                "ekoklas": self.ekoklas
                }
        return [platba]
    class Meta:
        verbose_name = 'Pravidelná platba'
        verbose_name_plural = 'Faktúry - Pravidelné platby'
    def __str__(self):
        return self.cislo

class Najomnik(PersonCommon):
    nazov = models.CharField("Názov", max_length=200)
    zastupeny = models.CharField("Zastúpený",
            max_length=200,
            blank = True,
            null = True,
            )
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Nájomník'
        verbose_name_plural = 'Prenájom - Nájomníci'
    def __str__(self):
        return self.nazov


class NajomnaZmluva(models.Model):
    oznacenie = "NZ"    #NZ-2021-123
    cislo = models.CharField("Číslo",
            #help_text: definovaný vo forms
            max_length=50)
    najomnik = models.ForeignKey(Najomnik,
            on_delete=models.PROTECT,
            verbose_name = "Nájomník"
            )
    url_zmluvy = models.URLField('URL zmluvy',
            help_text = "Zadajte URL pdf súboru zmluvy zo stránky CRZ.",
            null=True,
            blank = True
            )
    datum_zverejnenia_CRZ = models.DateField('Platná od',
            help_text = "Zadajte dátum účinnosti zmluvy (dátum zverejnenia v CRZ + 1 deň).",
            blank=True, null=True
            )
    datum_do = models.DateField('Platná do',
            help_text = "Nechajte prázdne alebo zadajte dátum ukončenia prenájmu (ukončenia platnosti zmluvy).<br />Po zadaní dátumu sa zmaže obsah polí <em>Miestnosti</em> a <em>Výmera miestností</em>",
            blank=True,
            null=True)
    miestnosti = models.CharField("Miestnosti",
            help_text = "Zadajte číslo prenajatej miestnosti alebo zoznam čísiel prenajatých miestností oddelených čiarkou",
            max_length=100,
            blank = True,
            null=True
            )
    vymery = models.CharField("Výmera miestností",
            help_text = "Zadajte výmeru prenajatej miestnosti alebo zoznam výmer v poradí podľa poľa <em>Miestnosti</em>",
            max_length=150,
            blank = True,
            null=True
            )
    poznamka = models.CharField("Poznámka",
            max_length=200,
            null=True,
            blank=True
            )
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Nájomná zmluva',
        verbose_name_plural = 'Prenájom - Zmluvy'
        #abstract = True
    def __str__(self):
        return f"{self.najomnik} - {self.cislo}"

class NajomneFaktura(Klasifikacia):
    # Polia
    oznacenie = "NF"    #NF-2021-123
    cislo = models.CharField("Číslo",
            #help_text: definovaný vo forms
            max_length=50)
    cislo_softip = models.CharField("Číslo Softip",
            help_text = "Zadajte číslo faktúry zo Softipu",
            max_length=25,
            blank = True,
            null=True)

    typ = models.CharField("Typ faktúry",
            max_length=25,
            choices=TypPN.choices)

    dane_na_uhradu = models.DateField('Dané na vybavenie dňa',
            help_text = 'Zadajte dátum odovzdania krycieho listu na sekretariát na odoslanie THS. <br />Vytvorí sa záznam v <a href="/admin/dennik/dokument/">denníku prijatej a odoslanej pošty</a>.',
            blank=True, null=True)
    splatnost_datum = models.DateField('Dátum splatnosti',
            help_text = "Zadajte dátum splatnosti 1. platby v aktuálnom roku.<br />Platby sú štvrťročné, po zadaní 1. faktúry (ak nejde o vyúčtovanie) sa doplnia záznamy pre zvyšné faktúry v roku.",
            null=True)
    suma = models.DecimalField("Suma bez DPH",
            help_text = 'Zadajte sumu bez DPH štrvrťročne.<br />Ak sa nájomníkovi účtuje DPH za nájomné, vypočíta sa z tejto sumy. DPH za služby sa účtuje vždy.',
            max_digits=8,
            decimal_places=2,
            null=True)
    dan = models.DecimalField("DPH",
            help_text = 'Zadajte sumu DPH štrvrťročne.<br />V prípade zmlúv uzavretých 07/2022 a neskôr sa DPH neúčtuje.',
            max_digits=8,
            decimal_places=2,
            default=0,
            null=True)
    zmluva = models.ForeignKey(NajomnaZmluva,
            null=True,
            verbose_name = "Nájomná zmluva",
            on_delete=models.PROTECT
            )
    platobny_prikaz = models.FileField("Krycí list pre THS-ku",
            help_text = "Súbor s krycím listom pre THS-ku. Generuje sa akciou 'Vytvoriť krycí list pre THS'.<br />Ak treba, v prípade vyúčtovania je súčasťou aj platobný prikaz",
            upload_to=platobny_prikaz_upload_location,
            null = True, blank = True)
    history = HistoricalRecords()

    # Koho uviesť ako adresata v denniku
    def adresat(self):
        return self.objednavka_zmluva.najomnik.nazov if self.objednavka_zmluva else ""

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        if not self.splatnost_datum: return []
        if self.splatnost_datum <zden: return []
        #if self.splatnost_datum >= date(zden.year, zden.month+1, zden.day): return []
        kdatum =  date(zden.year, zden.month+1, zden.day) if zden.month+1 <= 12 else  date(zden.year+1, 1, 1)
        if self.splatnost_datum >= kdatum: return []
        typ = "prenájom nájomné" if self.typ == TypPN.NAJOMNE else "prenájom služby" if self.typ == TypPN.SLUZBY else "prenájom vyúčtovanie"
        platba = {
                "nazov":f"Faktúra {typ}",
                "suma": self.suma,
                "datum": self.dane_na_uhradu,
                "subjekt": f"{self.zmluva.najomnik.nazov}, (za {zden.year}/{zden.month})", 
                "cislo": self.cislo,
                "zdroj": self.zdroj,
                "zakazka": self.zakazka,
                "ekoklas": self.ekoklas
                }
        return [platba]
    class Meta:
        verbose_name = 'Faktúra za prenájom'
        verbose_name_plural = 'Prenájom - Faktúry'

def bezprikazu_file_path(instance, filename):
    return os.path.join(BEZ_PRIKAZU_DIR, filename)
class PlatbaBezPrikazu(Klasifikacia):
    oznacenie = "PbP"
    cislo = models.CharField("Číslo", 
        #help_text = "Číslo rozpočtovej položky. Nová položka za pridáva len vtedy, keď položka s požadovanou klasifikáciou neexistuje.",  
        max_length=50)
    suma = models.DecimalField("Suma",
            help_text = 'Suma podľa výpisu zo Softipu. Výdavky uveďte ako záporné číslo.',
            max_digits=8,
            decimal_places=2,
            null=True)
    datum_platby = models.DateField('Dátum vyplatenia',
            help_text = "Dátum realizácie platby podľa výpisu zo Softipu",
            null=True)
    predmet = models.CharField("Popis platby", 
            help_text = "Stručný popis platby podľa výpisu zo Softipu.",
            max_length=100,
            null=True)
    subor = models.FileField("Priložený súbor",
            storage=OverwriteStorage(), 
            upload_to=bezprikazu_file_path, 
            null = True, 
            blank = True 
            )
    history = HistoricalRecords()

    #zarátanie dotácií, v roku len raz, v januári
    def cerpanie_rozpoctu(self, zden):
        if not str(zden.year) in self.cislo: return []
        if zden.month != 1: return []
        platba = {
                "nazov":f"Platba bez príkazu",
                "suma": self.suma,
                "datum": self.datum_platby,
                "subjekt": self.predmet,
                "cislo": self.cislo,
                "zdroj": self.zdroj,
                "zakazka": self.zakazka,
                "ekoklas": self.ekoklas
                }
        return [platba]

    class Meta:
        verbose_name = 'Platba bez platobného príkazu'
        verbose_name_plural = 'Platby bez platobného príkazu'
    def __str__(self):
        return f'{self.cislo}'

class RozpoctovaPolozka(Klasifikacia):
    oznacenie = "RP"
    cislo = models.CharField("Číslo", 
        #help_text = "Číslo rozpočtovej položky. Nová položka za pridáva len vtedy, keď položka s požadovanou klasifikáciou neexistuje.",  
        max_length=50)
    suma = models.DecimalField("Aktuálny súčet dotácií a prevodov",
            help_text = 'Automaticky vypočítaná položka. Nezohľadňuje prímy a výdavky',
            max_digits=8,
            decimal_places=2,
            null=True)
    history = HistoricalRecords()

    #zarátanie dotácií, v roku len raz, v januári
    def cerpanie_rozpoctu(self, zden):
        if not str(zden.year) in self.cislo: return []
        if zden.month != 1: return []
        platba = {
                "nazov":f"Dotácia",
                "suma": self.suma,
                "zdroj": self.zdroj,
                "zakazka": self.zakazka,
                "ekoklas": self.ekoklas
                }
        return [platba]

    class Meta:
        verbose_name = 'Rozpočtová položka'
        verbose_name_plural = 'Rozpočet - Rozpočtové položky'
    def __str__(self):
        return f'{self.cislo}'

class RozpoctovaPolozkaDotacia(Klasifikacia):
    oznacenie = "RPD"
    cislo = models.CharField("Číslo", 
        #help_text = "Číslo rozpočtovej položky. Nová položka za pridáva len vtedy, keď položka s požadovanou klasifikáciou neexistuje.",  
        max_length=50)
    suma = models.DecimalField("Výška dotácie",
            help_text = 'Suma sa pripočíta k zodpovedajúcej rozpočtovej položke za aktuálny rok. Ak tá ešte neexistuje, vytvorí sa.',
            max_digits=8,
            decimal_places=2,
            null=True)
    rozpoctovapolozka = models.ForeignKey(RozpoctovaPolozka,
            on_delete=models.PROTECT, 
            verbose_name = "Rozpočtová položka",
            null = True,
            related_name='%(class)s_rozpoctovapolozka')  #zabezpečí rozlíšenie modelov, keby dačo
    history = HistoricalRecords()

    def clean(self): 
        if self.suma < 0:
            raise ValidationError("Suma musí byť kladná")
        qs = RozpoctovaPolozka.objects.filter(
                zdroj=self.zdroj,
                program=self.program,
                zakazka=self.zakazka,
                cinnost=self.cinnost,
                ekoklas=self.ekoklas
            )
        if qs:
            qs[0].suma += self.suma
            qs[0].save()
            self.rozpoctovapolozka = qs[0]
        else:
            polozka = RozpoctovaPolozka(
                cislo = nasledujuce_cislo(RozpoctovaPolozka),
                zdroj=self.zdroj,
                program=self.program,
                zakazka=self.zakazka,
                cinnost=self.cinnost,
                ekoklas=self.ekoklas,
                suma=self.suma,
                )
            polozka.save()
            self.rozpoctovapolozka = polozka

    class Meta:
        verbose_name = 'Dotácia'
        verbose_name_plural = 'Rozpočet - Dotácie'
    def __str__(self):
        return f'{self.cislo}'

class RozpoctovaPolozkaPresun(models.Model):
    oznacenie = "RPP"
    cislo = models.CharField("Číslo", 
        #help_text = "Číslo rozpočtovej položky. Nová položka za pridáva len vtedy, keď položka s požadovanou klasifikáciou neexistuje.",  
        max_length=50)
    suma = models.DecimalField("Suma na presunutie",
            help_text = 'Suma sa presunie zo zdrojovej do cieľovej rozpočtovej položky',
            max_digits=8,
            decimal_places=2,
            null=True)
    zdroj = models.ForeignKey(RozpoctovaPolozka,
            on_delete=models.PROTECT, 
            verbose_name = "Z položky",
            null = True,
            related_name='%(class)s_zdroj')  #zabezpečí rozlíšenie modelov, keby dačo
    ciel = models.ForeignKey(RozpoctovaPolozka,
            help_text = 'Ak cieľová položka ešte neexistuje, vytvorte ju ako dotáciu s 0-ovou výškou.',
            on_delete=models.PROTECT, 
            verbose_name = "Do položky",
            null = True,
            related_name='%(class)s_ciel')  #zabezpečí rozlíšenie modelov, keby dačo
    dovod = models.CharField("Dôvod presunu", 
            max_length=200, 
            null=True)
    history = HistoricalRecords()

    def clean(self): 
        if self.suma < 0:
            raise ValidationError("Suma musí byť kladná")
        self.zdroj.suma -= self.suma
        self.ciel.suma += self.suma
        self.zdroj.save()
        self.ciel.save()

    class Meta:
        verbose_name = 'Presun medzi položkami'
        verbose_name_plural = 'Rozpočet - Presuny'
    def __str__(self):
        return f'{self.cislo}'

def prispevok_stravne_upload_location(instance, filename):
    return os.path.join(STRAVNE_DIR, filename)
class PrispevokNaStravne(Klasifikacia):
    oznacenie = "PS"    #v čísle faktúry, FS-2021-123
    cislo = models.CharField("Poradové číslo príspevku", max_length=50)
    za_mesiac = models.CharField("Za mesiac", 
            max_length=20, 
            help_text = "Zvoľte mesiac, za ktorý príspevok je. <br />Príspevok za január sa vypláca v decembri predchádzajúceho roku (v čísle príspevku má byť uvedený rok, v ktorom sa príspevok vyplácal).",
            null = True,
            choices=Mesiace.choices)
    suma_zamestnavatel = models.DecimalField("Príspevok (zrážka) zamestnávateľ", 
            help_text = "Príspevok zamestnávateľa (Ek. klas. 642014) na stravné.<br />Ak ide o vyplatenie zamestnancovi, uveďte zápornú hodnotu, ak ide o zrážku, tak kladnú hodnotu.",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    # Položka suma_socfond nemá Ek. klasifikáciu, soc. fond nie sú peniaze EnÚ
    suma_socfond = models.DecimalField("Príspevok (zrážka) soc. fond", 
            help_text = "Príspevok zo sociálneho fondu (Ek. klas. 642014) na stravné.<br />Ak ide o vyplatenie zamestnancovi, uveďte zápornú hodnotu, ak ide o zrážku, tak kladnú hodnotu.<br />Vytvorením Príspevku na stravné sa automaticky vytvorí položka sociálneho fondu.",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    po_zamestnancoch = models.FileField("Prehľad po zamestnancoch",
            help_text = "Súbor s mesačným prehľadom príspevkov na stravné po zamestnancoch",
            upload_to=prispevok_stravne_upload_location, 
            null = True)
    history = HistoricalRecords()

    # test platnosti dát
    def clean(self): 
        if self.suma_zamestnavatel * self.suma_socfond <= 0:
            raise ValidationError("Položky 'Príspevok zamestnávateľa' a 'Príspevok zo soc. fondu' musia byť buď len kladné alebo len záporné.")

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        if not str(zden.year) in self.cislo: return []
        if not self.za_mesiac: return []
        msc= {
            "januar": 1,
            "februar": 2,
            "marec": 3,
            "april": 4,
            "maj": 5,
            "jun": 6,
            "jul": 7,
            "august": 8,
            "september": 9,
            "oktober": 10,
            "november": 11,
            "december": 12
            }
        if zden.month != msc[self.za_mesiac]: return [] 
        platba = {
                "nazov":f"Stravné",
                "suma": self.suma_zamestnavatel,
                "datum": zden,
                "subjekt": "Zamestnanci",
                "cislo": self.cislo,
                "zdroj": self.zdroj,
                "zakazka": self.zakazka,
                "ekoklas": self.ekoklas
                }
        return [platba]

    class Meta:
        verbose_name = 'Príspevok na stravné'
        verbose_name_plural = 'PaM - Príspevky na stravné'
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
    zamestnanie_od = models.DateField('1. zamestnanie od',
            help_text = "Dátum nástupu do 1. zamestnania. Preberá sa zo Softipu, kde sa vypočíta z dátumu nástupu do EnÚ a započítanej praxe",
            blank=True,
            null=True)
    zamestnanie_enu_od = models.DateField('Zamestnanie v EnÚ od',
            help_text = "Dátum nástupu do zamestnania v EnÚ.",
            blank=True,
            null=True)
    vymeriavaci_zaklad = models.TextField("Denný vymeriavací základ", 
            help_text = "Zadajte po riadkoch denný vymeriavací základ podľa Softipu (PaM > PAM - Personalistika a Mzdy > Mzdy > Nemocenské dávky > Denný VZ €.<br />v tvare 'RRRR/MM suma (napr. '2022/02 30,4986').<br />Treba zadať len za mesiace, za ktoré má zamestnanec nárok na náhradu mzdy. Na chýbajúce údaje sa upozorní pri výpočte čerpania rozpočtu.", 
            max_length=500,
            blank=True,
            null=True)
    dds = models.CharField("Účastník DDS", 
            max_length=3, 
            help_text = "Uveďte 'Áno', ak sa zamestnanec zúčastňuje doplnkového dôchodkového sporenia.<br />V tom prípade vyplňte aj položku 'DDS od'",
            null = True,
            choices=AnoNie.choices,
            default=AnoNie.NIE)
    dds_od = models.DateField('DDS od',
            help_text = "Dátum, odkedy sa zamestnanec zúčastňuje doplnkového dôchodkového sporenia.",
            blank=True,
            null=True)
    history = HistoricalRecords()
    class Meta:
        verbose_name = "Zamestnanec"
        verbose_name_plural = "PaM - Zamestnanci"
    def __str__(self):
        return f"{self.priezvisko}, {self.meno}, Z"

class Dohodar(ZamestnanecDohodar):
    history = HistoricalRecords()
    class Meta:
        verbose_name = "Dohodár"
        verbose_name_plural = "PaM - Dohodári"
    def __str__(self):
        return f"{self.priezvisko}, {self.meno}, D"

def vymer_file_path(instance, filename):
    return os.path.join(PLATOVE_VYMERY_DIR, filename)

#Polymorphic umožní, aby DoVP a PrijataFaktura mohli použiť ObjednavkaZmluva ako ForeignKey
class PlatovyVymer(Klasifikacia):
    oznacenie = "PaM"
    cislo = models.CharField("Číslo výmeru", 
            help_text = "Uveďte číslo výmeru podľa THS",
            null = True,
            max_length=50)
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
    datum_od = models.DateField('Platný od',
            help_text = "Zadajte dátum začiatku platnosti výmeru",
            null=True)
    datum_do = models.DateField('Platný do',
            help_text = "Nechajte prázdne alebo zadajte dátum ukončenia prac. pomeru. Ak sa pre zamestnanca vytvorí nový výmer, toto pole v predchádzajúcom výmere sa vyplní automaticky, čím sa jeho platnosť ukončí",
            blank=True,
            null=True)
    tarifny_plat = models.DecimalField("Tarifný plat", 
            help_text = "Tarifný plat podľa prílohy č. 5 Zákona č. 553/2003 Z. z. (Zákon o odmeňovaní niektorých zamestnancov pri výkone práce vo verejnom záujme)",
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
    uvazok = models.DecimalField("Úväzok týždenne", 
            help_text = "Zadajte týždenný pracovný úväzok. Napríklad, pri plnom úväzku 37,5 hod, pri polovičnom 18,75 hod",
            max_digits=8, 
            decimal_places=2)
    uvazok_denne = models.DecimalField("Úväzok denne", 
            help_text = "Zadajte denný pracovný úväzok. Napríklad, pri plnom úväzku 7,5 hod, pri polovičnom úväzku a dohodnutých 3 prac. dňoch týždenne 6,25 hod (3*6,25= 18,75)",
            max_digits=8, 
            decimal_places=2 )
    zamestnanieroky = models.IntegerField("Doba zamestnania v Enú (roky)",
            help_text = "Pole sa vyplňuje automaticky, ak je pole 'Dátum do' vyplnené. Vtedy toto pole obsahuje počet celých rokov zamestnania v EnÚ do konca platnosti tohoto výmeru",
            blank=True,
            null=True)
    zamestnaniedni = models.IntegerField("Doba zamestnania v EnÚ (dni)",
            help_text = "Pole sa vyplňuje automaticky, ak je pole 'Dátum do' vyplnené. Vtedy toto pole obsahuje počet dní zamestnania neúplného posledného roku do konca platnosti tohoto výmeru.",
            blank=True,
            null=True)
    datum_postup = models.DateField('Pl. postup',
            help_text = "Dátum najbližšieho platového postupu. Pole sa vyplňuje automaticky, ak nie je pole 'Dátum do' vyplnené, inak je prázdne",
            blank=True,
            null=True)
    zmena_zdroja = models.TextField("Zmena zdroja", 
            help_text = "Zadajte po riadkoch mesiace (v rozsahu platnosti výmeru), v ktorých sa zdroj odlišuje od preddefinovaného zdroja.<br /> Napr. ak je preddefinovaný zdroj 111, ale vo februári 2022 sa vyplácalo zo zdroja 42, na riadku uveďte '2022/02 42'.", 
            max_length=500,
            blank=True,
            null=True)
    history = HistoricalRecords()

    def polozka_cerpania(self, nazov, rekapitulacia, suma, zden, zdroj=None, zakazka=None, ekoklas=None):
        return {
            "nazov": nazov,
            "rekapitulacia": rekapitulacia,
            "suma": round(Decimal(suma),2),
            "zdroj": zdroj if zdroj else self.zdroj,
            "zakazka": zakazka if zakazka else self.zakazka,
            "datum": zden if zden < date.today() else None,
            "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}, (za {zden.year}/{zden.month})", 
            "cislo": self.cislo if self.cislo else "-",
            "ekoklas": EkonomickaKlasifikacia.objects.get(kod=ekoklas) if ekoklas else self.ekoklas
            }

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        if zden < self.datum_od: return []
        if self.datum_do and zden > self.datum_do: return []

        #zobrať do úvahy neprítomnosť za daný mesiac
        qs = Nepritomnost.objects.filter(zamestnanec=self.zamestnanec)
        qs1 = qs.exclude(nepritomnost_do__lt=zden)  # vylúčiť nevyhovujúce
        next_month = zden + relativedelta(months=1, day=1)  # 1. deň nasl. mesiaca
        qs2 = qs1.exclude(nepritomnost_od__gte=next_month)  # vylúčiť nevyhovujúce

        ddov = 0         #počet dní dovolenky. Za všetky sa platí náhrada mzdy vo výške platu
        dosob = 0        #Počet dní osobných prekážok v práci (lekár a podobne). Platí sa náhrada mzdy vo výške platu 
        dnepl = 0        #neplatené dni. Materská, PN a neplatené voľno. Náhrada za PN sa ráta inak
        dpn1 = 0         #počet dní práceneschopnosti v dňoch 1-3. Platí sa náhrada 55 %
        dpn2 = 0         #počet dní práceneschopnosti v dňoch 4-10. Platí sa náhrada 80 %

        pdni = int(self.uvazok/self.uvazok_denne)    #počet pracovných dní v týždni, napr. 18.85/6.25=3
        for nn in qs2:  #môže byť viac neprítomností za mesiac
            #v prípade neukončenej neprítomnosti predpokladať neprítomnosť do konca mesiaca
            if not nn.nepritomnost_do:  #nie je zadaný
                posledny=next_month - relativedelta(days=1) # koniec mesiaca
            else:
                posledny = nn.nepritomnost_do 
            # posledný deň obmedziť koncom mesiaca
            if posledny >= next_month:
                posledny = next_month - relativedelta(days=1) 
            prvy = nn.nepritomnost_od if nn.nepritomnost_od>zden else zden

            #Vypočítať počet dní neprítomnosti
            #Predpokladáme, že v prípade, keď zamestnanec pracuje len napr. Utorok - Štvrtok, neprítomnosť je zadaná len na tieto dni
            if nn.nepritomnost_typ == TypNepritomnosti.DOVOLENKA2:
                ddov += 0.5
            elif nn.nepritomnost_typ == TypNepritomnosti.DOVOLENKA:
                ddov += prac_dni(prvy,posledny, pdni, zahrnut_sviatky=False)    #Sviatky sa nezarátajú do dovolenky, ale ako bežný prac. deň
            elif nn.nepritomnost_typ == TypNepritomnosti.PN:
                dnepl += prac_dni(prvy,posledny, pdni, zahrnut_sviatky=True)    #Sviatky sa do PN zarátajú, náhrada sa ráta inak
                #Prvé 3 dni, 55%
                dpn1 += prekryv_dni(zden, nn.nepritomnost_od, nn.nepritomnost_od+timedelta(days=2))
                #Dni 4 až 10, 80%
                dpn2 += prekryv_dni(zden, nn.nepritomnost_od+timedelta(days=3), min(nn.nepritomnost_od+timedelta(days=9), posledny))
            elif nn.nepritomnost_typ in [TypNepritomnosti.MATERSKA, TypNepritomnosti.OCR, TypNepritomnosti.NEPLATENE]:
                dnepl += prac_dni(prvy,posledny, pdni, zahrnut_sviatky=True)    #Sviatky sa zarátajú, nie sú platené
            elif nn.nepritomnost_typ in [TypNepritomnosti.LEKARDOPROVOD, TypNepritomnosti.LEKAR]:
                dosob += float(nn.dlzka_nepritomnosti*prac_dni(prvy,posledny, pdni, zahrnut_sviatky=True)/self.uvazok_denne)    #Osobné prekážky vo sviatok sa nemajú čo vyskytovať
            else:   #Osobné prekážky (Pracovné voľno)
                dosob += prac_dni(prvy,posledny, pdni, zahrnut_sviatky=True)    #Osobné prekážky vo sviatok sa nemajú čo vyskytovať

        if zden == date(2022,7,1) and self.zamestnanec.meno=="Helena":
            print(self.zamestnanec.priezvisko, ddov, dosob, dnepl, dpn1, dpn2)
            #trace()
            pass
        #Počet pracovných dní
        #pri častočnom úväzku len približné, na presný výpočet by sme asi potrebovali vedieť, v ktorých dňoch zamestnanec pracuje.
        #Tento údaj nie je ani v Softipe
        dprac = prac_dni(zden, ppd=pdni, zahrnut_sviatky=False) #Sviatky sa rátajú ako pracovné dni

        koef_prac = 1 - float(ddov+dosob+dnepl) / dprac    #Koeficient odpracovaných dní
        koef_osob = dosob / dprac
        koef_dov = float(ddov / dprac)    #počet prac dní v rámci dovolenky / počet prac. dní v mesiaci

        #súbor s tabuľku odvodov
        nazov_objektu = "Odvody zamestnancov a dohodárov"  #Presne takto musí byť objekt pomenovaný
        objekt = SystemovySubor.objects.filter(subor_nazov = nazov_objektu)
        if not objekt:
            return f"V systéme nie je definovaný súbor '{nazov_objektu}'."
        nazov_suboru = objekt[0].subor.file.name 

        #Konverzia typu dochodku na pozadovany typ vo funkcii ZamestnanecOdvodySpolu
        td = self.zamestnanec.typ_doch
        td_konv = "InvDoch30" if td==TypDochodku.INVALIDNY30 else "InvDoch70" if td== TypDochodku.INVALIDNY70 else "StarDoch" if td==TypDochodku.STAROBNY else "VyslDoch" if td==TypDochodku.INVAL_VYSL else "Bezny"

        zdroj = None
        zakazka = None
        if self.zmena_zdroja:
            if zden == date(2022,2,1):
                #trace()
                pass
            zz = re.findall(r"%s/0*%s +([0-9]*)"%(zden.year, zden.month), self.zmena_zdroja)
            if zz:
                if zz[0]== "42":
                    zdroj = Zdroj.objects.get(kod="42")
                    zakazka = TypZakazky.objects.get(kod="42002200")
                elif zz[0]== "111":
                    zdroj = Zdroj.objects.get(kod="111")
                    zakazka = TypZakazky.objects.get(kod="11010001 spol. zák.")

        zdroj = zdroj if zdroj else self.zdroj
        zakazka = zakazka if zakazka else self.zakazka

        #Odpracované dni
        tarifny = {
                "nazov":"Plat tarifný plat",
                "rekapitulacia":  "Tarifný plat",
                "suma": -round(Decimal(koef_prac*float(self.tarifny_plat)),2),
                "zdroj": zdroj,
                "zakazka": zakazka,
                "datum": zden if zden < date.today() else None,
                "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}, (za {zden.year}/{zden.month})", 
                "cislo": self.cislo if self.cislo else "-",
                "ekoklas": self.ekoklas
                }
        osobny = {
                "nazov": "Plat osobný príplatok",
                "rekapitulacia": "Osobný príplatok",
                "suma": -round(Decimal(koef_prac*float(self.osobny_priplatok)),2),
                "zdroj": zdroj,
                "zakazka": zakazka,
                "datum": zden if zden < date.today() else None,
                "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}, (za {zden.year}/{zden.month})", 
                "cislo": self.cislo if self.cislo else "-",
                "ekoklas": EkonomickaKlasifikacia.objects.get(kod="612001")
                }
        funkcny = {
                "nazov": "Plat príplatok za riadenie",
                "rekapitulacia": "Príplatok za riadenie",
                "suma": -round(Decimal(koef_prac*float(self.funkcny_priplatok)),2),
                "zdroj": zdroj,
                "zakazka": zakazka,
                "datum": zden if zden < date.today() else None,
                "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}, (za {zden.year}/{zden.month})", 
                "cislo": self.cislo if self.cislo else "-",
                "ekoklas": EkonomickaKlasifikacia.objects.get(kod="612002")
                }
        tabulkovy_plat = float(self.tarifny_plat) + float(self.osobny_priplatok) + float(self.funkcny_priplatok)
        dds_prispevok = None
        dds_zdravotne = None
        if self.zamestnanec.dds == AnoNie.ANO:
            if not self.zamestnanec.dds_od:
                dds_prispevok["poznamka"] = f"Vypočítaná suma výšky príspevku do DDS je nesprávna. V údajoch zamestnanca '{self.zamestnanec}' treba vyplniť pole 'DDS od'"
            else: # Príspevok do DDS sa vypláca od 1. dňa mesiaca, keď bola uzatvorena dohoda
                dds_od = date(self.zamestnanec.dds_od.year, self.zamestnanec.dds_od.month, 1)
            if zden >= dds_od:
                dds_prispevok = self.polozka_cerpania("DDS príspevok", "DDS", -DDS_PRISPEVOK*koef_prac*tabulkovy_plat/100, zden, zdroj=zdroj, zakazka=zakazka, ekoklas="627")
                _, _, zdravpoist, _ = ZamestnanecOdvody(nazov_suboru, float(dds_prispevok['suma']), td_konv, zden)
                ekoklas = "621" if self.zamestnanec.poistovna == Poistovna.VSZP else "623"
                dds_zdravotne = self.polozka_cerpania("DDS poistenie zdravotné", "Zdravotné poistné", zdravpoist['zdravotne'], zden, zdroj=zdroj, zakazka=zakazka, ekoklas=ekoklas)

        #PN
        nahrada_pn = None
        if dpn1 or dpn2:
            denny_vz, text_vz = self.urcit_VZ(zden)
            nahrada_pn = {
                    "nazov": "Náhrada mzdy - PN",
                    "suma": -round(Decimal((dpn1*PN1+dpn2*PN2)*denny_vz/100),2),
                    "rekapitulacia": "DPN",
                    "zdroj": zdroj,
                    "zakazka": zakazka,
                    "datum": zden if zden < date.today() else None,
                    "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}, (za {zden.year}/{zden.month})", 
                    "cislo": self.cislo if self.cislo else "-",
                    "ekoklas": EkonomickaKlasifikacia.objects.get(kod="642015")
                    }
            if text_vz and "približne" in text_vz:
                nahrada_pn["poznamka"] = f"Vypočítaná suma náhrad PN je približná. V údajoch zamestnanca '{self.zamestnanec}' treba doplniť denný vymeriavací základ za mesiac {zden.year}/{zden.month}."

        #Osobné prekážky
        nahrada_osob = None
        if dosob:
            nahrada_osob = {
                    "nazov": "Náhrada mzdy - osobné prekážky",
                    "rekapitulacia": "Prekážky osobné",
                    "suma": -round(Decimal(tabulkovy_plat*koef_osob),2),
                    "zdroj": zdroj,
                    "zakazka": zakazka,
                    "datum": zden if zden < date.today() else None,
                    "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}, (za {zden.year}/{zden.month})", 
                    "cislo": self.cislo if self.cislo else "-",
                    "ekoklas": EkonomickaKlasifikacia.objects.get(kod="640")    #Overiť klasifikáciu
                    }

        nahrada_dov = None
        if ddov:
            nahrada_dov = {
                    "nazov": "Náhrada mzdy - dovolenka",
                    "rekapitulacia": "Dovolenka",
                    "suma": -round(Decimal(koef_dov*tabulkovy_plat),2),
                    "zdroj": zdroj,
                    "zakazka": zakazka,
                    "datum": zden if zden < date.today() else None,
                    "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}, (za {zden.year}/{zden.month})", 
                    "cislo": self.cislo if self.cislo else "-",
                    "ekoklas": EkonomickaKlasifikacia.objects.get(kod="611")
                    }

        if zden==date(2022,4,1):
            pass
        socpoist, _, zdravpoist, _ = ZamestnanecOdvody(nazov_suboru, (koef_prac+koef_dov+koef_osob) * tabulkovy_plat, td_konv, zden)
        ekoklas = "621" if self.zamestnanec.poistovna == Poistovna.VSZP else "623"
        zdravotne = self.polozka_cerpania("Plat poistenie zdravotné", f"Zdravotné poistné", -zdravpoist['zdravotne'], zden, zdroj=zdroj, zakazka=zakazka, ekoklas=ekoklas)
        socialne=[]
        for item in socpoist:
            socialne.append(self.polozka_cerpania("Plat poistenie sociálne", f"Sociálne poistné", -socpoist[item], zden, zdroj=zdroj, zakazka=zakazka, ekoklas=item))

        #Socfond
        if zden in [date(2022,1,1), date(2022,2,1), date(2022,3,1)]:   #Počas tychto 3 mesiacov bolo všetko inak :D
            socfond = {
                "nazov": "Prídel do SF",
                "rekapitulacia": "Sociálny fond",
                "suma": -round(Decimal(0.015*koef_prac*tabulkovy_plat),2),
                "zdroj": Zdroj.objects.get(kod="131L"), 
                "zakazka": TypZakazky.objects.get(kod="131L0001"),
                "datum": zden if zden < date.today() else None,
                "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}, (za {zden.year}/{zden.month})", 
                "cislo": self.cislo if self.cislo else "-",
                "ekoklas": EkonomickaKlasifikacia.objects.get(kod="637016")
                }
        else:
            socfond = {
                "nazov": "Prídel do SF",
                "rekapitulacia": "Sociálny fond",
                "suma": -round(Decimal(0.015*koef_prac*tabulkovy_plat),2),  #0.015 podľa kolektívnej zmluvy
                "zdroj": zdroj,
                "zakazka": zakazka,
                "datum": zden if zden < date.today() else None,
                "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}, (za {zden.year}/{zden.month})", 
                "cislo": self.cislo if self.cislo else "-",
                "ekoklas": EkonomickaKlasifikacia.objects.get(kod="637016")
                }
        #if koef_prit_sf < 1 and zden == date(2022,11,1):
        #if zden == date(2022,5,1) and nahrada_dov:
            #print(self.zamestnanec.priezvisko,tabulkovy_plat, socfond['suma'], poistne['suma'],tarifny['suma'], osobny['suma'], funkcny['suma'], nahrada_dov['suma'])

        retlist = socialne + [tarifny, osobny, funkcny, zdravotne, socfond]
        if dds_prispevok: retlist.append(dds_prispevok)
        if dds_zdravotne: retlist.append(dds_zdravotne)
        if nahrada_dov: retlist.append(nahrada_dov)
        if nahrada_osob: retlist.append(nahrada_osob)
        if nahrada_pn: retlist.append(nahrada_pn)
        return retlist

    def urcit_VZ(self, mesiac):
        tabulkovy_plat = float(self.tarifny_plat) + float(self.osobny_priplatok) + float(self.funkcny_priplatok)
        if self.zamestnanec.vymeriavaci_zaklad:
            vz = re.findall(r"%s/0*%s ([0-9,]*)"%(mesiac.year, mesiac.month), self.zamestnanec.vymeriavaci_zaklad)
            if vz:
                return float(vz[0].replace(",",".")), "Náhrada mzdy - PN"
        return 12*tabulkovy_plat/365, "Náhrada mzdy - PN (približne)"

    class Meta:
        verbose_name = "Platový výmer"
        verbose_name_plural = "PaM - Platové výmery"
    def __str__(self):
        od = self.datum_od.strftime('%d. %m. %Y') if self.datum_od else '--'
        return f"{self.zamestnanec.priezvisko}, {od}"

class Nepritomnost(models.Model):
    oznacenie = "Np"
    cislo = models.CharField("Číslo", 
            #help_text: definovaný vo forms
            null = True,
            max_length=50)
    zamestnanec = models.ForeignKey(Zamestnanec,
            on_delete=models.PROTECT, 
            verbose_name = "Zamestnanec",
            related_name='%(class)s_zamestnanec')  #zabezpečí rozlíšenie modelov, keby dačo
    nepritomnost_od= models.DateField('Neprítomnosť od',
            help_text = 'Prvý deň neprítomnosti',
            null=True)
    nepritomnost_do= models.DateField('Neprítomnosť do',
            help_text = 'Posledný deň neprítomnosti',
            blank=True, 
            null=True)
    nepritomnost_typ = models.CharField("Typ neprítomnosti",
            max_length=20, 
            null=True, 
            choices=TypNepritomnosti.choices)
    dlzka_nepritomnosti = models.DecimalField("Dĺžka nepritomnosti",
            help_text = "Dĺžka neprítomnosti v hodinách, napr '1,5'.<br /> Vypĺňa sa len v prípade návštevy lekára a doprovodu k lekárovi.<br />Ak v týchto prípadoch pole necháte prázdne, automaticky sa doplní na denný úväzok zamestnanca.", 
            max_digits=4, 
            decimal_places=2, 
            blank=True, 
            null=True)
    history = HistoricalRecords()
    class Meta:
        verbose_name = "Neprítomnosť"
        verbose_name_plural = "PaM - Neprítomnosť"
    def __str__(self):
        od = self.nepritomnost_od.strftime('%d. %m. %Y')
        return f"{self.zamestnanec.priezvisko} od {od}"

    def clean(self): 
        if self.nepritomnost_typ in [TypNepritomnosti.LEKAR, TypNepritomnosti.LEKARDOPROVOD]:
            if self.nepritomnost_do - self.nepritomnost_od > timedelta(0): 
                raise ValidationError("Neprítonmosť v prípade návštevy u lekára alebo doprovodu k lekárovi možno zadať len na jeden deň.")

def odmena_upload_location(instance, filename):
    return os.path.join(ODMENY_DIR, filename)
class OdmenaOprava(Klasifikacia):
    oznacenie = "OO"
    cislo = models.CharField("Číslo", 
            #help_text: definovaný vo forms
            null = True,
            max_length=50)
    typ = models.CharField("Odmena/Oprava",
            max_length=20, 
            help_text = "Uveďte, či ide o odmenu a opravu vyplatenej mzdy",
            null = True,
            choices=OdmenaAleboOprava.choices)
    zamestnanec = models.ForeignKey(Zamestnanec,
            on_delete=models.PROTECT, 
            verbose_name = "Zamestnanec",
            related_name='%(class)s_zamestnanec')  #zabezpečí rozlíšenie modelov, keby dačo
    suma = models.DecimalField("Suma", 
            help_text = "Výška odmeny alebo opravy. Odmena je záporná, oprava môže byť kladná (t.j. zmestnancovi bola strhnutá z výplaty).",
            max_digits=8, 
            decimal_places=2, 
            null=True,
            default=0)
    vyplatene_v_obdobi = models.CharField("Vyplatené v", 
            help_text = "Uveďte mesiac vyplatenia odmeny alebo mesiac, ku ktorému sa oprava vzťahuje v tvare em>MM/RRRR</em>", 
            null = True,
            max_length=10)
    zdovodnenie = models.TextField("Zdôvodnenie", 
            help_text = "Zadajte dôvod vyplatenia odmeny alebo vykonania opravy",
            max_length=500,
            null=True)
    subor_kl = models.FileField("Príkaz a krycí list",
            help_text = "Súbor s príkazom na vyplatenie odmeny a krycím listom.<br />Generuje sa akciou <em>Vytvoriť príkaz na vyplatenie odmeny</em>.",
            upload_to=odmena_upload_location,
            blank=True, 
            null=True
            )
    datum_kl = models.DateField('Dátum odoslania KL',
            help_text = "Dátum odoslania krycieho listu.<br />Po zadaní sa vytvorí záznam v Denníku.",
            blank=True, 
            null=True
            )
    history = HistoricalRecords()

    @staticmethod
    def check_vyplatene_v(value):
        return re.findall(r"[0-9][0-9]/[0-9][0-9][0-9][0-9]", value)

    def clean(self): 
        if self.typ == OdmenaAleboOprava.ODMENA and self.suma >= 0:
            raise ValidationError("Suma odmeny musí byť záporná")

        if self.vyplatene_v_obdobi:
            if not OdmenaOprava.check_vyplatene_v(self.vyplatene_v_obdobi):
                raise ValidationError("Údaj v poli 'Vyplatené v' musí byť v tvare MM/RRRR (napr. 07/2022)")

    def polozka_cerpania(self, nazov, rekapitulacia, suma, zden, zdroj=None, zakazka=None, ekoklas=None):
        return {
            "nazov": nazov,
            "rekapitulacia": rekapitulacia,
            "suma": round(Decimal(suma),2),
            "zdroj": zdroj if zdroj else self.zdroj,
            "zakazka": zakazka if zakazka else self.zakazka,
            "datum": zden if zden < date.today() else None,
            "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}, (za {zden.year}/{zden.month})", 
            "cislo": self.cislo if self.cislo else "-",
            "ekoklas": EkonomickaKlasifikacia.objects.get(kod=ekoklas) if ekoklas else self.ekoklas
            }

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        if self.vyplatene_v_obdobi != "%02d/%d"%(zden.month, zden.year): return []

        platby = []
        #súbor s tabuľku odvodov
        nazov_objektu = "Odvody zamestnancov a dohodárov"  #Presne takto musí byť objekt pomenovaný
        objekt = SystemovySubor.objects.filter(subor_nazov = nazov_objektu)
        if not objekt:
            return f"V systéme nie je definovaný súbor '{nazov_objektu}'."
        nazov_suboru = objekt[0].subor.file.name

        if self.typ == OdmenaAleboOprava.ODMENA:
            nazov = "Plat odmena"
            rekapitulacia = "Odmeny"
        elif self.typ == OdmenaAleboOprava.OPRAVATARIF:
            nazov = "Plat tarifný plat oprava"
            rekapitulacia = "Tarifný plat"
        elif self.typ == OdmenaAleboOprava.OPRAVAOSOB:
            nazov = "Plat osobný príplatok oprava"
            rekapitulacia = "Osobný príplatok"
        elif self.typ == OdmenaAleboOprava.OPRAVARIAD:
            nazov = "Plat príplatok za riadenie oprava"
            rekapitulacia = "Príplatok za riadenie"

        platba = {
            "nazov": nazov,
            "rekapitulacia": rekapitulacia,
            "suma": self.suma,
            "datum": zden,
            "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}", 
            "cislo": self.cislo,
            "zdroj": self.zdroj,
            "zakazka": self.zakazka,
            "ekoklas": self.ekoklas
            }
        platby.append(platba)

        #Konverzia typu dochodku na pozadovany typ vo funkcii ZamestnanecOdvodySpolu
        td = self.zamestnanec.typ_doch
        td_konv = "InvDoch30" if td==TypDochodku.INVALIDNY30 else "InvDoch70" if td== TypDochodku.INVALIDNY70 else "StarDoch" if td==TypDochodku.STAROBNY else "VyslDoch" if td==TypDochodku.INVAL_VYSL else "Bezny"
        socpoist, _, zdravpoist, _ = ZamestnanecOdvody(nazov_suboru, float(self.suma), td_konv, zden)
        ekoklas = "621" if self.zamestnanec.poistovna == Poistovna.VSZP else "623"
        zdravotne = self.polozka_cerpania("Plat poistenie zdravotné", f"Zdravotné poistné", zdravpoist['zdravotne'], zden, ekoklas=ekoklas)
        platby.append(zdravotne)

        for item in socpoist:
            platby.append(self.polozka_cerpania("Plat poistenie sociálne", f"Sociálne poistné", socpoist[item], zden, ekoklas=item))

        #Socfond
        if zden in [date(2022,1,1), date(2022,2,1), date(2022,3,1)]:   #Počas tychto 3 mesiacov bolo všetko inak :D
            socfond = self.polozka_cerpania("Prídel do SF", "Sociálny fond", round(Decimal(0.015*float(self.suma))), zden, zdroj=Zdroj.objects.get(kod="131L"), zakazka=TypZakazky.objects.get(kod="131L0001"), ekoklas="637016")
        else:
            socfond = self.polozka_cerpania("Prídel do SF", "Sociálny fond", round(Decimal(0.015*float(self.suma))), zden, ekoklas="637016")
        platby.append(socfond)

        return platby

    class Meta:
        verbose_name = "Odmena alebo oprava"
        verbose_name_plural = "PaM - Odmeny a opravy"
    def __str__(self):
        return f"{self.zamestnanec.priezvisko}"

def rekreacia_upload_location(instance, filename):
    return os.path.join(REKREACIA_DIR, filename)
class PrispevokNaRekreaciu(Klasifikacia):
    oznacenie = "PnR"
    cislo = models.CharField("Číslo", 
            #help_text: definovaný vo forms
            null = True,
            max_length=50)
    datum = models.DateField('Dátum prijatia žiadosti',
            help_text = "Dátum prijatia žiadosti",
            null=True
            )
    zamestnanec = models.ForeignKey(Zamestnanec,
            on_delete=models.PROTECT, 
            verbose_name = "Zamestnanec",
            related_name='%(class)s_zamestnanec')  #zabezpečí rozlíšenie modelov, keby dačo
    subor_ziadost = models.FileField("Žiadosť o príspevok",
            help_text = "Súbor so žiadosťou o príspevok (doručený zamestnancom).<br />Po zadaní sa vytvorí záznam v Denníku.",
            upload_to=rekreacia_upload_location
            )
    subor_vyuctovanie = models.FileField("Vyúčtovanie príspevku",
            help_text = "Súbor s vyúčtovaním príspevku (doručený mzdovou účtárňou).<br />Po zadaní sa vytvorí záznam v Denníku.",
            upload_to=rekreacia_upload_location,
            blank=True, 
            null=True
            )
    prispevok = models.DecimalField("Príspevok na vyplatenie", 
            help_text = "Výška príspevku na rekreáciu určená mzdovou účtárňou (záporné číslo).",
            max_digits=8, 
            decimal_places=2, 
            blank=True, 
            null=True,
            default=0)
    vyplatene_v_obdobi = models.CharField("Vyplatené v", 
            help_text = "Uveďte obdobie vyplatenia podľa vyúčtovania v tvare MM/RRRR (napr. 07/2022)",
            null = True,
            blank=True, 
            max_length=10)
    subor_kl = models.FileField("Krycí list",
            help_text = "Súbor s krycím listom.<br />Generuje sa akciou <em>Vytvoriť krycí list</em> po vyplnení položky <em>Príspevok na vyplatenie</em>",
            upload_to=rekreacia_upload_location,
            blank=True, 
            null=True
            )
    datum_kl = models.DateField('Dátum odoslania KL',
            help_text = "Dátum odoslania krycieho listu.<br />Po zadaní sa vytvorí záznam v Denníku.",
            blank=True, 
            null=True
            )

    @staticmethod
    def check_vyplatene_v(value):
        return re.findall(r"[0-9][0-9]/[0-9][0-9][0-9][0-9]", value)


    def clean(self): 
        if self.prispevok > 0:
            raise ValidationError("Suma príspevku musí byť záporná")
        if self.subor_vyuctovanie and not self.prispevok:
            raise ValidationError("Ak je vložený súbor s vyúčtovaním, treba vyplniť aj položky 'Príspevok na vyplatenie'")

        if not self.subor_vyuctovanie and self.prispevok:
            raise ValidationError("Ak je vyplnená položka 'Príspevok na vyplatenie', treba vložiť súbor s vyúčtovaním.")

        if not self.subor_vyuctovanie and self.vyplatene_v_obdobi:
            raise ValidationError("Ak je vyplnená položka 'Príspevok na vyplatenie', treba vyplniť aj pole 'Vyplatené v'.")

        if not self.subor_vyuctovanie and self.vyplatene_v_obdobi:
            raise ValidationError("Ak je vyplnená položka 'Vyplatené v', treba vložiť súbor s vyúčtovaním.")

        if self.vyplatene_v_obdobi:
            if not PrispevokNaRekreaciu.check_vyplatene_v(self.vyplatene_v_obdobi):
                raise ValidationError("Údaj v poli 'Vyplatené v' musí byť v tvare MM/RRRR (napr. 07/2022)")

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        qs = PrispevokNaRekreaciu.objects.filter(vyplatene_v_obdobi = "%02d/%d"%(zden.month, zden.year))
        suma = 0
        for q in qs:
            suma += q.prispevok
        if not suma: return []
        platba = {
                "nazov": "Príspevok na rekreáciu",
                "suma": suma,
                "datum": self.datum,
                "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}", 
                "cislo": self.cislo,
                "zdroj": self.zdroj,
                "zakazka": self.zakazka,
                "ekoklas": self.ekoklas
                }
        return [platba]

    class Meta:
        verbose_name = "Príspevok na rekreáciu"
        verbose_name_plural = "PaM - Príspevky na rekreáciu"
    def __str__(self):
        return f"{self.zamestnanec.priezvisko}"

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
    stav_dohody = models.CharField(max_length=20,
            #help_text = "Z ponuky zvoľte aktuálny stav zmluvy. Autorský honorár môže byť vyplatený len vtedy, keď je v stave 'Platná / Zverejnená v CRZ.",
            help_text = 'Aktuálny stav dohody, <font color="#aa0000">správne nastaviť po každej jeho zmene</font>.',
            choices=StavDohody.choices, default=StavDohody.NOVA)
    dohoda_odoslana= models.DateField('Dohodárovi na podpis ',
            help_text = 'Dátum odovzdania dohody na sekretariát na odoslanie na podpis (poštou). Vytvorí sa záznam v <a href="/admin/dennik/dokument/">denníku prijatej a odoslanej pošty</a>.',
            null=True)
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
            help_text = "Dátum odoslania podkladov na vyplatenie, vypĺňa sa automaticky pri vyplnení položky 'PAM Vyplatenie dohody'",
            null = True, blank = True,
            max_length=200)
    subor_dohody = models.FileField("Vygenerovaná dohoda",
            help_text = "Súbor s textom dohody. Generuje sa akciou 'Vytvoriť subor dohody'",
            upload_to=dohoda_upload_location, 
            null = True, blank = True)
    sken_dohody = models.FileField("Skenovaná dohoda",
            help_text = "Súbor s podpísanou dohodou, treba naskenovať",
            upload_to=dohoda_upload_location, 
            null = True, blank = True)
    # Koho uviesť ako adresata v denniku
    def adresat(self):
        return self.zmluvna_strana

    def polozka_cerpania(self, nazov, rekapitulacia, suma, zden, zdroj=None, zakazka=None, ekoklas=None):
        return {
            "nazov": nazov,
            "rekapitulacia": rekapitulacia,
            "suma": round(Decimal(suma),2),
            "zdroj": zdroj if zdroj else self.zdroj,
            "zakazka": zakazka if zakazka else self.zakazka,
            "datum": zden if zden < date.today() else None,
            "subjekt": f"{self.zmluvna_strana.priezvisko}, {self.zmluvna_strana.meno}, (za {zden.year}/{zden.month})", 
            "cislo": self.cislo if self.cislo else "-",
            "ekoklas": EkonomickaKlasifikacia.objects.get(kod=ekoklas) if ekoklas else self.ekoklas
            }

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
            null=True)
    hod_celkom = models.DecimalField("Predpokl. počet hodín",
            help_text = "Uveďte predpokladaný celkový počet odpracovaných hodín, najviac 350.",
            max_digits=8, 
            decimal_places=1, 
            null=True)
    id_tsh = models.CharField("Číslo priradené THS",
            help_text = "Uveďte číslo, pod ktorým dohody vedie THS",
            null = True, blank = True,
            max_length=100)
    pomocnik = models.CharField("Pomoc rod. príslušníkov", 
            help_text = "Uveďte zoznam rod. príslušníkov, ktorí budú pomáhať pri vykonávaní činnosti, alebo nechajte prázdne. Pre každého uveďte meno a priezvisko.",
            null = True, blank = True,
            max_length=100)
    history = HistoricalRecords()

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        if self.datum_do <zden: return []
        kdatum =  date(zden.year, zden.month+1, zden.day) if zden.month+1 <= 12 else  date(zden.year+1, 1, 1)
        if self.datum_do >= kdatum: return []
        platba = {
                "nazov":f"DoVP odmena",
                "rekapitulacia": "DoVP",
                "suma": -Decimal(self.odmena_celkom),
                "datum": zden,
                "subjekt": f"{self.zmluvna_strana.priezvisko}, {self.zmluvna_strana.meno}", 
                "cislo": self.cislo,
                "zdroj": self.zdroj,
                "zakazka": self.zakazka,
                "ekoklas": self.ekoklas
                }

        nazov_objektu = "Odvody zamestnancov a dohodárov"  #Presne takto musí byť objekt pomenovaný
        objekt = SystemovySubor.objects.filter(subor_nazov = nazov_objektu)
        if not objekt:
            return f"V systéme nie je definovaný súbor '{nazov_objektu}'."
        nazov_suboru = objekt[0].subor.file.name 
        td = self.zmluvna_strana.typ_doch
        td_konv = "StarDoch" if td==TypDochodku.STAROBNY else "InvDoch" if td== TypDochodku.INVALIDNY else "StarDoch" if td==TypDochodku.STAROBNY else "DoVP"
        socpoist, _, zdravpoist, _  = DohodarOdvody(nazov_suboru, float(self.odmena_celkom), td_konv, zden, ODVODY_VYNIMKA if self.vynimka == AnoNie.ANO else 0)
        ekoklas = "621" if self.zmluvna_strana.poistovna == Poistovna.VSZP else "623"
        zdravotne = self.polozka_cerpania("DoVP poistenie zdravotné", "Zdravotné poistné", -zdravpoist['zdravotne'], zden, ekoklas=ekoklas)
        socialne=[]
        for item in socpoist:
            socialne.append(self.polozka_cerpania("DoVP poistenie sociálne", "Sociálne poistné", -socpoist[item], zden, ekoklas=item))
        return socialne + [platba, zdravotne]
 
    # test platnosti dát
    def clean(self): 
        num_days = (self.datum_do - self.datum_od).days
        if num_days > 366:
            raise ValidationError(f"Doba platnosti dohody presahuje maximálnu povolenú dobu 12 mesiacov.")
        if self.hod_celkom > 350:
            raise ValidationError(f"Celkový počet {pocet_hodin} hodín maximálny zákonom povolený povolený počet 350.")

    class Meta:
        verbose_name = 'Dohoda o vykonaní práce'
        verbose_name_plural = 'PaM - Dohody o vykonaní práce'
    def __str__(self):
        return f"{self.zmluvna_strana}; {self.cislo}"

class DoBPS(Dohoda):
    oznacenie = "DoBPS"
    odmena_celkom = models.DecimalField("Celková suma v EUR", 
            help_text = "Zadajte celkovú odmenu za vykonanú prácu. Bude vyplatená po odovzdaní práce a výkazu",
            max_digits=8, 
            decimal_places=2, 
            null=True)
    hod_mesacne = models.DecimalField("Predpokl. počet hodín mesačne",
            help_text = "Uveďte predpokladaný priemerný počet odpracovaných hodín. Počet nesmie v priemere prekračovať 80 hodín mesačne",
            max_digits=8, 
            decimal_places=1, 
            null=True)
    datum_ukoncenia = models.DateField('Dátum ukončenia',
            help_text = "Zadajte dátum predčasného ukončenia platnosti dohody",
            blank = True,
            null=True)
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Dohoda o bigádnickej práci študentov'
        verbose_name_plural = 'PaM - Dohody o bigádnickej práci študentov'
    def __str__(self):
        return f"{self.zmluvna_strana}; {self.cislo}"

class DoPC(Dohoda):
    oznacenie = "DoPC"
    dodatok_k = models.ForeignKey('self',
            help_text = "Ak ide len o dodatok k existujúcej DoVP, zadajte ju v tomto poli.<br />V tomto prípade sa pri ukladaní číslo tohohto dodatku zmení na číslo dohody doplnené o text 'Dodatok'. <br />Ďalší postup vytvárania dodatku je rovnaký ako v prípade DoVP",
            on_delete=models.PROTECT,
            related_name='%(class)s_dopc',
            blank = True,
            null = True
            )
    odmena_mesacne = models.DecimalField("Odmena za mesiac",
            help_text = "Dohodnutá mesačná odmena",
            max_digits=8,
            decimal_places=2, 
            null=True)
    hod_mesacne = models.DecimalField("Hodín za mesiac",
            help_text = "Dohodnutý počet odpracovaných hodín za mesiac, najviac 40",
            max_digits=8, 
            decimal_places=1, 
            null=True)
    datum_ukoncenia = models.DateField('Dátum ukončenia',
            help_text = "Zadajte dátum predčasného ukončenia platnosti dohody",
            blank = True,
            null=True)
    zmena_zdroja = models.TextField("Zmena zdroja alebo odmeny", 
            help_text = "Zadajte po riadkoch mesiace (v rozsahu platnosti dohody), v ktorých sa zdroj alebo suma odlišujú od svojich preddefinovaných hodnôt, a to v tvare <em>RRRR/MM zdroj odmena</em>.<br />Vždy treba zadať zdroj aj odmenu, aj keď sa zmenila len jedna z týchto hodnôt.", 
            max_length=500,
            blank=True,
            null=True)
    history = HistoricalRecords()

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        if zden < self.datum_od: return []
        if self.datum_ukoncenia and zden > self.datum_ukoncenia: return []
        if zden > self.datum_do: return []

        zdroj = None
        zakazka = None
        odmena_mesacne = None
        if self.zmena_zdroja:
            if zden == date(2022,5,1):
                #trace()
                pass
            zz = re.findall(r"%s/0*%s +([0-9]+) +([0-9,.]+)"%(zden.year, zden.month), self.zmena_zdroja)
            if zz:
                if zz[0][0]== "42":
                    zdroj = Zdroj.objects.get(kod="42")
                    zakazka = TypZakazky.objects.get(kod="42002200")
                    odmena_mesacne = float(zz[0][1].replace(",","."))
                elif zz[0][0]== "111":
                    zdroj = Zdroj.objects.get(kod="111")
                    zakazka = TypZakazky.objects.get(kod="11010001 spol. zák.")
                    odmena_mesacne = float(zz[0][1].replace(",","."))

        zdroj = zdroj if zdroj else self.zdroj
        zakazka = zakazka if zakazka else self.zakazka
        odmena_mesacne = odmena_mesacne if odmena_mesacne else self.odmena_mesacne
        platba = {
                "nazov":f"DoPC odmena",
                "rekapitulacia": "DoPC",
                "suma": -Decimal(odmena_mesacne),
                "datum": zden,
                "subjekt": f"{self.zmluvna_strana.priezvisko}, {self.zmluvna_strana.meno}", 
                "cislo": self.cislo,
                "zdroj": zdroj,
                "zakazka": zakazka,
                "ekoklas": self.ekoklas
                }
        nazov_objektu = "Odvody zamestnancov a dohodárov"  #Presne takto musí byť objekt pomenovaný
        objekt = SystemovySubor.objects.filter(subor_nazov = nazov_objektu)
        if not objekt:
            return f"V systéme nie je definovaný súbor '{nazov_objektu}'."
        nazov_suboru = objekt[0].subor.file.name 
        td = self.zmluvna_strana.typ_doch
        td_konv = "StarDoch" if td==TypDochodku.STAROBNY else "InvDoch" if td== TypDochodku.INVALIDNY else "StarDoch" if td==TypDochodku.STAROBNY else "DoPC"
        socpoist, _, zdravpoist, _ = DohodarOdvody(nazov_suboru, float(odmena_mesacne), td_konv, zden, ODVODY_VYNIMKA if self.vynimka == AnoNie.ANO else 0)
        ekoklas = "621" if self.zmluvna_strana.poistovna == Poistovna.VSZP else "623"
        zdravotne = self.polozka_cerpania("DoPC poistenie zdravotné", "Zdravotné poistné", -zdravpoist['zdravotne'], zden, zdroj=zdroj, zakazka=zakazka, ekoklas=ekoklas)
        socialne=[]
        for item in socpoist:
            socialne.append(self.polozka_cerpania("DoPC poistenie sociálne", f"Sociálne poistné", -socpoist[item], zden, zdroj=zdroj, zakazka=zakazka, ekoklas=item))
        return socialne + [platba, zdravotne]

    class Meta:
        verbose_name = 'Dohoda o pracovnej činnosti'
        verbose_name_plural = 'PaM - Dohody o pracovnej činnosti'
    # test platnosti dát
    def clean(self): 
        if self.hod_mesacne > 40:
            raise ValidationError(f"Počet hodín mesačne {hod_mesacne} presahuje maximálny zákonom povolený počet 40.")

        if self.dodatok_k and not "Dodatok" in self.cislo:
            qs = DoPC.objects.filter(cislo__startswith=self.dodatok_k.cislo).order_by("cislo")
            #1. položka nie je dodatok, DoPC-2022-001
            self.cislo = f"{self.dodatok_k.cislo[:13]}-Dodatok-{len(qs)}" 
            #ukončiť predchádzajúcu
            qlast = qs.last()
            qlast.datum_ukoncenia = self.datum_od + timedelta(days = -1) 
            qlast.save()

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
        #Treba zistiť, ako sa to vlastne ráta - či ide o kalendárne mesiace alebo treba zohladnit alikvotnu cast
        if self.dohoda.vynimka and td in ["DoPC", "DoBPSForm"]:
            vynimka_suma = ODVODY_VYNIMKA    #vyplacané mesačne, fixná suma vynimky
        elif self.dohoda.vynimka and td in ["DoVP"]:
            #datum_do je posledný deň práce, preto + 1
            pocet_mesiacov = 12*(self.dohoda.datum_do-self.dohoda.datum_od+timedelta(days=1)).days/365
            vynimka_suma = ODVODY_VYNIMKA * pocet_mesiacov
            pass
        else:
            vynimka_suma = 0    #bez výnimky

        #dochodok (musí byť umiestnené ZA vypočtom vynimka_suma
        if self.dohoda.zmluvna_strana.typ_doch in [TypDochodku.STAROBNY, TypDochodku.PREDCASNY, TypDochodku.VYSLUHOVY]:
            td = "StarDoch"
        elif self.dohoda.zmluvna_strana.typ_doch in [TypDochodku.INVALIDNY, TypDochodku.INVAL_VYSL]:
            td = "InvDoch"

        vyplatena_odmena = float(self.vyplatena_odmena)
        socialne_zam, socialne_prac, zdravotne_zam, zdravotne_prac = DohodarOdvody(nazov_suboru, vyplatena_odmena, td, self.dohoda.datum_od, vynimka_suma) 
        self.poistne_zamestnavatel = socialne_zam+zdravotne_zam
        self.poistne_dohodar = socialne_praczdravotne_prac
        self.dan_dohodar = (vyplatena_odmena - self.poistne_dohodar) * DAN_Z_PRIJMU / 100
        self.na_ucet = vyplatena_odmena - self.poistne_dohodar - self.dan_dohodar

        #uložiť dátum vyplatenia do dohody. V prípade opakovaného vyplácania DoPC a DoBPS sa pridáva ďalší dátum do zoznamu
        vypl = "%s, "%self.dohoda.vyplatene if self.dohoda.vyplatene else ""
        self.dohoda.vyplatene=f"{vypl}{self.datum_vyplatenia}"
        self.dohoda.save()
        pass

    class Meta:
        verbose_name = 'Vyplatenie dohody'
        verbose_name_plural = 'PaM - Vyplácanie dohôd'


def pokladna_upload_location(instance, filename):
    return os.path.join(VPD_DIR, filename)
class Pokladna(models.Model):
    oznacenie = "Po"
    cislo = models.CharField("Číslo záznamu", 
        max_length=50)
    typ_transakcie = models.CharField("Typ transakcie", 
            max_length=25, 
            null=True, 
            choices=TypPokladna.choices
            )
    suma = models.DecimalField("Suma",
            help_text = 'Suma. Dotácia je kladná, suma výdavku je záporná',
            max_digits=8,
            decimal_places=2,
            null=True
            )
    datum_transakcie = models.DateField('Dátum transakcie',
            help_text = "Dátum prijatia dotácie alebo preplatenia výdavku",
            null=True
            )
    cislo_VPD = models.IntegerField("Poradové číslo VPD",
            blank = True,
            null = True
        )
    zamestnanec = models.ForeignKey(Zamestnanec,
            help_text = "Uveďte zamestnanca, ktorého výdavok bol uhradený. V prípade dotácie nechajte prázdne.", 
            on_delete=models.PROTECT,
            related_name='%(class)s_pokladna',
            blank = True,
            null = True
            )
    subor_vpd = models.FileField("Súbor VPD",
            help_text = "Súbor s VPD. Generuje sa akciou 'Vytvoriť VPD'",
            upload_to=pokladna_upload_location, 
            null = True, blank = True)
    datum_softip = models.DateField('Dátum THS',
            help_text = "Dátum vytvorenia zoznamu VPD pre THS. Vypĺňa sa automaticky akciou 'vytvoriť zoznam VPD pre THS'",
            blank = True,
            null=True
            )
    popis = models.CharField("Popis platby", 
            help_text = "Stručný popis transakcie.",
            max_length=30,
            null=True
            )
    poznamka = models.CharField("Poznámka", 
            max_length=60,
            blank = True,
            null=True
            )
    zdroj = models.ForeignKey(Zdroj,
            help_text = "V prípade výdavku je pole povinné, v prípade dotácie nechajte prázdne",
            on_delete=models.PROTECT,
            related_name='%(class)s_pokladna',
            blank = True,
            null = True
            )
    zakazka = models.ForeignKey(TypZakazky,
            on_delete=models.PROTECT,
            help_text = "V prípade výdavku je pole povinné, v prípade dotácie nechajte prázdne",
            verbose_name = "Typ zákazky",
            related_name='%(class)s_pokladna',
            blank = True,
            null = True
            )
    ekoklas = models.ForeignKey(EkonomickaKlasifikacia,
            on_delete=models.PROTECT,
            help_text = "V prípade výdavku je pole povinné, v prípade dotácie nechajte prázdne",
            verbose_name = "Ekonomická klasifikácia",
            related_name='%(class)s_pokladna',
            blank = True,
            null = True
            )
    cinnost = models.ForeignKey(Cinnost,
            on_delete=models.PROTECT,
            help_text = "V prípade výdavku je pole povinné, v prípade dotácie nechajte prázdne",
            verbose_name = "Činnosť",
            related_name='%(class)s_pokladna',
            blank = True,
            null = True
            )
    history = HistoricalRecords()

    def clean(self): 
        chyby={}
        if self.typ_transakcie == TypPokladna.DOTACIA:
            if self.suma <= 0:
                chyby["suma"] = "V prípade dotácie musí byť pole 'Suma' kladné"
        else:
            if not self.cislo_VPD:
                self.cislo_VPD = nasledujuce_VPD()
            if self.suma >= 0:
                chyby["suma"] = "V prípade VPD musí byť pole 'Suma' záporné"
            if not self.zamestnanec:
                chyby["zamestnanec"] = "V prípade VPD treba pole 'Zamestnanec' vyplniť"
            if not self.zakazka:
                chyby["zakazka"] = "V prípade VPD treba pole 'Typ zákazky' vyplniť"
            if not self.zdroj:
                chyby["zdroj"] = "V prípade VPD treba pole 'Zdroj' vyplniť"
            if not self.ekoklas:
                chyby["ekoklas"] = "V prípade VPD treba pole 'Ekonomická klasifikácia' vyplniť"
            if not self.cinnost:
                chyby["cinnost"] = "V prípade VPD treba pole 'Činnosť' vyplniť"
            pass
        if chyby:
            raise ValidationError(chyby)

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        if self.typ_transakcie == TypPokladna.DOTACIA: return []
        if not self.datum_softip: return []
        if self.datum_softip <zden: return []
        kdatum =  date(zden.year, zden.month+1, zden.day) if zden.month+1 <= 12 else  date(zden.year+1, 1, 1)
        if self.datum_softip >= kdatum: return []
        platba = {
                "nazov": "Pokladňa",
                "suma": self.suma,
                "datum": self.datum_transakcie,
                "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}", 
                "cislo": self.cislo,
                "zdroj": self.zdroj,
                "zakazka": self.zakazka,
                "ekoklas": self.ekoklas
                }
        return [platba]

    class Meta:
        verbose_name = 'Záznam pokladne'
        verbose_name_plural = 'Záznamy pokladne'
    def __str__(self):
        return f'{self.cislo}'

class SocialnyFond(models.Model):
    oznacenie = "SF"
    cislo = models.CharField("Číslo", 
            null = True,
            max_length=50)
    suma = models.DecimalField("Suma",
            help_text = 'Príjmy uveďte ako kladné číslo, výdavky uveďte ako záporné číslo.',
            max_digits=8,
            decimal_places=2,
            null=True)
    datum_platby = models.DateField('Dátum operácie',
            help_text = "Dátum realizácie operácie",
            null=True)
    predmet = models.CharField("Popis operácie", 
            help_text = "Stručný popis operácie.",
            max_length=100,
            null=True)
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Operácia na účte sociálneho fondu'
        verbose_name_plural = 'Sociálny fond'
    def __str__(self):
        return f'{self.cislo}'
