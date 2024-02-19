from django.db import models

from django.core.exceptions import ValidationError

#záznam histórie
#https://django-simple-history.readthedocs.io/en/latest/admin.html
from simple_history.models import HistoricalRecords
from uctovnictvo.storage import OverwriteStorage
from .rokydni import mesiace, koef_neodprac_dni, prekryv_dni, prac_dni
from polymorphic.models import PolymorphicModel
from django.utils.safestring import mark_safe
from django.urls import reverse
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
PERCENTAGE_VALIDATOR = [MinValueValidator(0), MaxValueValidator(100)]

from beliana.settings import TMPLTS_DIR_NAME, PLATOVE_VYMERY_DIR, DOHODY_DIR, PRIJATEFAKTURY_DIR, PLATOBNE_PRIKAZY_DIR, STRAVNE_HOD
from beliana.settings import ODVODY_VYNIMKA, DAN_Z_PRIJMU, OBJEDNAVKY_DIR, STRAVNE_DIR, REKREACIA_DIR
from beliana.settings import PN1, PN2, BEZ_PRIKAZU_DIR, DDS_PRISPEVOK, ODMENY_DIR, NEPRITOMNOST_DIR, SOCFOND_PRISPEVOK
from beliana.settings import VYSTAVENEFAKTURY_DIR, NAJOMNEFAKTURY_DIR, POKLADNA_DIR
import os,re
from datetime import timedelta, date, datetime
from dateutil.relativedelta import relativedelta
import numpy as np
from ipdb import set_trace as trace

#access label: AnoNie('ano').label
class OdmenaAleboOprava(models.TextChoices):
    ODMENA = 'odmena', 'Odmena'
    ODMENAS = 'odmenasubor', 'XLSX súbor s odmenami'
    OPRAVATARIF = 'opravatarif', 'Oprava tarifný plat'
    OPRAVAOSOB = 'opravaosob', 'Oprava osobný pr.'
    OPRAVARIAD = 'opravariad', 'Oprava pr. za riadenie'
    OPRAVAZR = 'opravazr', 'Oprava zrážky - plat'
    ODSTUPNE = 'odstupne', 'Odstupné'
    ODCHODNE = 'odchodne', 'Odchodné'
    DOVOLENKA = 'dovolenka', 'Náhrada mzdy - dovolenka'

#access label: AnoNie('ano').label
class PlatovaStupnica(models.TextChoices):
    ZAKLADNA = 'zakladna', 'Základná'
    OSOBITNA = 'osobitna', 'Osobitná'

#access label: AnoNie('ano').label
class AnoNie(models.TextChoices):
    ANO = 'ano', 'Áno'
    NIE = 'nie', 'Nie'

class Mena(models.TextChoices):
    EUR = 'EUR'
    CZK = 'CZK'
    USD = 'USD'
    GBP = 'GBP'

class SadzbaDPH(models.TextChoices):
    P20 = "20", "20 %"
    P10 = "10", "10 %"
    P5 = "5", "5 %"
    P0 = "0", "0 %"
    def __str__(self): return self.label

priblizny_kurz = {
        Mena.CZK: 24.36,
        Mena.USD: 1.045,
        Mena.GBP: 0.857
    }

class Stravne(models.TextChoices):
    PRISPEVKY = "prispevky", "Príspevky na stravné"
    ZRAZKY = "zrazky", "Zrážky za stravné"

# Pre triedu classname určí číslo nasledujúceho záznamu v tvare X-2021-NNN
def nasledujuce_cislo(classname, rok=None):
        # zoznam faktúr s číslom "PS-2021-123" zoradený vzostupne
        if rok:
            ozn_rok = f"{classname.oznacenie}-{rok}-"
        else:
            ozn_rok = f"{classname.oznacenie}-{datetime.now().year}-"
        itemlist = classname.objects.filter(cislo__istartswith=ozn_rok).order_by("cislo")
        if itemlist:
            # Takto podivne nájsť posledné číslo, lebo order_by zlyhá pri počte väčšom ako 1000
            # a posledná položka v itemlist má číslo 999
            nove_cislo = 0
            for item in itemlist:
                akt_cislo = int(re.findall(f"{ozn_rok}([0-9]+)",item.cislo)[0])
                if akt_cislo > nove_cislo:
                    nove_cislo = akt_cislo
            return "%s%03d"%(ozn_rok, nove_cislo+1)
        else:
            #sme v novom roku alebo trieda este nema instanciu
            return f"{ozn_rok}001"

        # Pre triedu classname určí číslo nasledujúceho záznamu v pvare X-2021-NNN

# Pre triedu Zmluva určí číslo nasledujúceho záznamu v tvare ZE-2021-NNN
def nasledujuce_Zmluva(rok=None):
        # zoznam faktúr s číslom "PS-2021-123" zoradený vzostupne
        if rok:
            ozn_rok = f"{Zmluva.oznacenie}-{rok}-"
        else:
            ozn_rok = f"{Zmluva.oznacenie}-{datetime.now().year}-"
        itemlist = Zmluva.objects.filter(nase_cislo__istartswith=ozn_rok).order_by("nase_cislo")
        if itemlist:
            latest = itemlist.last().nase_cislo
            nove_nase_cislo = int(re.findall(f"{ozn_rok}([0-9]+)",latest)[0]) + 1
            return "%s%03d"%(ozn_rok, nove_nase_cislo)
        else:
            #sme v novom roku alebo trieda este nema instanciu
            return f"{ozn_rok}001"

# nasledujúce číslo Výdavkového pokladničného dokladu
def nasledujuce_VPD():
        # zoznam VPD zoradený podľa cislo_VPD vzostupne
        ozn_rok = f"{Pokladna.oznacenie}-{datetime.now().year}-"
        qs = Pokladna.objects.filter(cislo__istartswith=ozn_rok, typ_transakcie=TypPokladna.VPD)
        itemlist=qs.exclude(cislo_VPD__isnull=True).order_by("cislo_VPD")
        return itemlist.last().cislo_VPD+1 if itemlist else 1

# nasledujúce číslo Výdavkového pokladničného dokladu
def nasledujuce_PPD():
        # zoznam PPD zoradený podľa cislo_VPD vzostupne
        ozn_rok = f"{Pokladna.oznacenie}-{datetime.now().year}-"
        qs = Pokladna.objects.filter(cislo__istartswith=ozn_rok ,typ_transakcie=TypPokladna.PPD)
        itemlist=qs.exclude(cislo_VPD__isnull=True).order_by("cislo_VPD")
        return itemlist.last().cislo_VPD+1 if itemlist else 1

#ak sa doplni stav pred 'PODPISANA_ENU', treba doplniť test vo funkcii vytvorit_subory_zmluvy
class StavDohody(models.TextChoices):
    NOVA = "nova", "Nová"                        #Stav dohody po vytvorení
    VYTVORENA = "vytvorena", "Vytvorená"                        #Stav dohody po vytvorení súboru. Treba dať na podpis
    #PODPISANA_ENU = "podpisana_enu", "Podpísaná EnÚ"
    NAPODPIS = "napodpis", "Daná na podpis vedeniu EnÚ"
    ODOSLANA_DOHODAROVI = "odoslana_dohodarovi", "Daná dohodárovi na podpis"
    PODPISANA_DOHODAROM = "podpisana_dohodarom", "Podpísaná dohodárom"
    DOKONCENA = "dokoncena", "Dokončená"

class TypNepritomnosti(models.TextChoices):
    MATERSKA = "materská", "Materská"           #Náhrada mzdy - prekážky osobné
    OCR = "ocr", "OČR"                          #NP
    PN = "pn", "PN"                             #Náhrada mzdy - prekážky osobné
    DOVOLENKA = "dovolenka", "Dovolenka"        #Náhrada mzdy - dovolenka
    DOVOLENKA2 = "dovolenka2", "Poldeň dovolenky"
    LEKAR = "lekar", "Návšteva u lekára (L)"    #Náhrada mzdy - prekážky osobné
    LEKARDOPROVOD = "lekardoprovod", "Doprovod k lekárovi (L/D)"  #Náhrada mzdy - prekážky osobné
    PZV = "pzv", "Platené zdr. voľno podľa KZ"    #Náhrada mzdy - prekážky osobné
    PV = "pv", "Pracovné voľno (PV, P, S, KZVS, POH)"    #Náhrada mzdy - prekážky osobné
    NEPLATENE = "neplatene", "Neplatené voľno"  # nič sa neplatí
    SLUZOBNA = "sluzobna", "Služobná cesta"     # normálna mzda
    PRACADOMA = "pracadoma", "Práca na doma"    # normálna mzda
    SKOLENIE = "skolenie", "Školenie"           # normálna mzda

#access label: AnoNie('ano').label
class TypPokladna(models.TextChoices):
    DOTACIA = 'prijem_do_pokladne', 'Príjem do pokladne'
    VPD = 'vystavenie_vpd', 'Výdavkový PD'
    PPD = 'vystavenie_ppd', 'Príjmový PD'

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

mesiace_num= {
    "januar": [1, Mesiace.JANUAR],
    "februar": [2, Mesiace.FEBRUAR],
    "marec": [3, Mesiace.MAREC],
    "april": [4, Mesiace.APRIL],
    "maj": [5, Mesiace.MAJ],
    "jun": [6, Mesiace.JUN],
    "jul": [7, Mesiace.JUL],
    "august": [8, Mesiace.AUGUST],
    "september": [9, Mesiace.SEPTEMBER],
    "oktober": [10, Mesiace.OKTOBER],
    "november": [11, Mesiace.NOVEMBER],
    "december": [12, Mesiace.DECEMBER]
    }

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

class GetAdminURL():
    def get_admin_url(self):
        # the url to the Django admin form for the model instance
        info = (self._meta.app_label, self._meta.model_name)
        url = reverse('admin:%s_%s_change' % info, args=(self.pk,))
        return mark_safe(f'<a href="{url}">{self.cislo}</a>')

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
                <li>možnosť: s 5 poľami oddelenými bodkočiarkou v poradí: <b>názov položky</b>; <b>merná jednotka</b> - ks, kg, l, m, m2, m3; <b>množstvo</b>; <b>cena za jednotku bez DPH; CPV kód</b>, napr. <strong>Euroobal A4; bal; 10; 7,50; 30193300-1</strong>. <br />Cena za jednotlivé položky a celková suma sa dopočíta. Pri výpočte sa berie do úvahy, či dodávateľ účtuje alebo neúčtuje cenu s DPH. </li>\
                <li>možnosť: ako jednoduchý text s jednou bodkočiarkou, za ktorou nasleduje CPV kód, napr. <strong>Objednávame tovar podľa priloženej ponuky / priloženého zoznamu; 45321000-3</strong>.<br />Súbor takejto ponuky alebo zoznamu vložte do poľa <em>Súbor prílohy</em> a <strong>predpokladanú cenu bez DPH</strong> vložte do poľa <em>Predpokladaná cena</em>.</li>\
                </ol>"),

            max_length=5000, null=True, blank=True)
    predpokladana_cena = models.DecimalField("Predpokladaná cena", 
            help_text = "Zadajte predpokladanú cenu bez DPH, ak už nie je zadaná v poli <em>Objednané položky</em>. <br />Vo vygenerovanej objednávke sa zoberie do úvahy, či dodávateľ účtuje alebo neúčtuje cenu s DPH.",
            max_digits=8, 
            decimal_places=2, 
            null=True, blank=True)
    datum_odoslania = models.DateField('Dátum odoslania',
            help_text = "Zadajte dátum odoslania objednávky. Po zadaní dátumu sa vytvorí záznam v Denníku prijatej a odoslanej pošty",
            blank=True, null=True)
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

    def clean(self):
        # test počtu riadkov v objednane_polozky
        pocet_riadkov = 18 #definované v common.VytvoritSuborObjednavky.pocet_riadkov
        pocet_poloziek = len(self.objednane_polozky.split("\r\n"))
        if pocet_poloziek > pocet_riadkov:
            raise ValidationError({
                "objednane_polozky":f"Zadaných bolo {pocet_poloziek} položiek. Maximálny povolený počet je {pocet_riadkov}."
                }
            )
        objednane = self.objednane_polozky.split("\n")
        pocet_poli = len(objednane[0].split(";"))
        if not pocet_poli in (2,5):
            raise ValidationError({
                "objednane_polozky":f"Prvá položka má {pocet_poli} polí, povolený počet je 2 alebo 5 (skontrolujte bodkočiarky)"
                }
            )
        for rr, polozka in enumerate(objednane):
            pp = len(polozka.split(";"))
            if pp != pocet_poli:
                raise ValidationError({
                    "objednane_polozky":f"Položka na riadku {rr+1} má {pp} polí, povolený počet je {pocet_poli}  (skontrolujte bodkočiarky)"
                    }
                )
        if pocet_poli == 2 and not self.predpokladana_cena:
            raise ValidationError({
                "predpokladana_cena":f"Ak položka v <em>Objednané položky</em> má len dve polia, tak toto pole musí byť vyplnené."
                }
            )

    class Meta:
        verbose_name = 'Objednávka'
        verbose_name_plural = 'Faktúry - Objednávky'
    def __str__(self):
        return f"{self.dodavatel}, objednávka, {self.cislo}"

class Rozhodnutie(ObjednavkaZmluva):
    datum_vydania = models.DateField('Dátum vydania',
            help_text = "Zadajte dátum vyvydania rozhodnutia/povolenia",
            default=datetime.now,
            blank=True, null=True)
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Rozhodnutie / Povolenie'
        verbose_name_plural = 'Faktúry - Rozhodnutia a povolenia'
    def __str__(self):
        return f"{self.dodavatel} - Ro/Po - {self.cislo}"

class Zmluva(ObjednavkaZmluva):
    oznacenie = "ZE"    #v čísle faktúry, ZE-2021-123
    nase_cislo = models.CharField("Naše číslo", 
            #help_text: definovaný vo forms
            null=True,
            max_length=50)
    url_zmluvy = models.URLField('URL zmluvy', 
            help_text = "Zadajte URL pdf súboru zmluvy zo stránky CRZ.",
            null=True,
            blank = True)
    datum_zverejnenia_CRZ = models.DateField('Platná od', 
            help_text = "Zadajte dátum účinnosti zmluvy (dátum zverejnenia v CRZ + 1 deň).",
            blank=True, null=True)
    trvala_zmluva = models.CharField("Trvalá zmluva", 
            max_length=3, 
            help_text = "Uveďte 'Áno', ak ide o trvalú zmluvu (očakáva sa viacero faktúr), inak uveďte 'Nie'.<br /><strong>Ak zmluva nahrádza staršiu zmluvu, treba jej platnosť ukončiť vyplnením poľa 'Platná do'.</strong> ",
            default = AnoNie.ANO,
            choices=AnoNie.choices)
    platna_do = models.DateField('Platná do', 
            help_text = "Zadajte dátum ukončenia platnosti trvalej zmluvy. Platnosť trvalej zmluvy sa testuje pri vytváraní faktúry.",
            blank=True, null=True)
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


#Klasifikácia pre prípad dvoch zdrojov
class Klasifikacia2(Klasifikacia):
    zdroj2 = models.ForeignKey(Zdroj,
            help_text = "Druhý zdroj v prípade delenia faktúry, inak nechajte prázdne",
            verbose_name = "Zdroj 2",
            on_delete=models.PROTECT,
            related_name='%(class)s_klasifikacia2',  
            blank = True,
            null = True
            )
    zakazka2 = models.ForeignKey(TypZakazky,
            help_text = "Druhá zákazka v prípade delenia faktúry, inak nechajte prázdne",
            on_delete=models.PROTECT,
            verbose_name = "Typ zákazky 2",
            related_name='%(class)s_klasifikacia2',
            blank = True,
            null = True
            )
    podiel2 = models.DecimalField(max_digits=5, 
            help_text = "Podiel druhého zdroja/zákazky v prípade delenia faktúry, inak 0 %",
            verbose_name = "Podiel 2",
            decimal_places=2, 
            default=Decimal(0), 
            blank = True,
            null = True,
            validators=PERCENTAGE_VALIDATOR)
    def clean(self):
        # test, či sú všetky vyplnené alebo či sú všetky prázdne
        values =[not self.zdroj2 is None, not self.zakazka2 is None, self.podiel2 != Decimal(0.00)]
        if len(set(values)) > 1:
            raise ValidationError({
                "zdroj2":"Polia 'Zdroj 2', 'Typ zákazky 2' a 'Podiel 2' musia byť buď všetky vyplnené alebo žiadne nesmie byť vyplnené",
                "zakazka2":"Polia 'Zdroj 2', 'Typ zákazky 2' a 'Podiel 2' musia byť buď všetky vyplnené alebo žiadne nesmie byť vyplnené", 
                "podiel2":"Polia 'Zdroj 2', 'Typ zákazky 2' a 'Podiel 2' musia byť buď všetky vyplnené alebo žiadne nesmie byť vyplnené", 
                }
            )

    class Meta:
        abstract = True

#https://stackoverflow.com/questions/55543232/how-to-upload-multiple-files-from-the-django-admin
#Vykoná sa len pri vkladaní suborov cez GUI. Pri programovom vytváraní treba cestu nastaviť
def platobny_prikaz_upload_location(instance, filename):
    return os.path.join(PLATOBNE_PRIKAZY_DIR, filename)
class Platba(models.Model):
    # Polia
    cislo = models.CharField("Číslo", 
            #help_text: definovaný vo forms
            max_length=50)
    dane_na_uhradu = models.DateField('Dané na úhradu dňa',
            help_text = 'Zadajte dátum odovzdania podpísaného platobného príkazu a krycieho listu na sekretariát na odoslanie THS. <br />Vytvorí sa záznam v <a href="/admin/dennik/dokument/">denníku prijatej a odoslanej pošty</a>.',
            blank=True, null=True)
    uhradene_dna = models.DateField('Uhradené dňa',
            help_text = 'Zadajte dátum uhradenia učtárňou (podľa výpisu zo Softipu a tak podobne',
            blank=True, null=True)
    splatnost_datum = models.DateField('Dátum splatnosti',
            null=True)
    suma = models.DecimalField("Suma", 
            max_digits=8, 
            decimal_places=2, 
            null=True)
    sadzbadph = models.CharField("Sadzba DPH", 
            max_length=10, 
            help_text = "Uveďte sadzbu DPH.",
            #help_text = "Uveďte sadzbu DPH. Ak je faktúra v režime prenesenia daňovej povinnosti zadajte 20 %",
            null = True,
            choices=SadzbaDPH.choices)
    platobny_prikaz = models.FileField("Platobný príkaz pre THS-ku",
            help_text = "Súbor s platobným príkazom a krycím listom pre THS-ku. Generuje sa akciou 'Vytvoriť platobný príkaz a krycí list pre THS'",
            upload_to=platobny_prikaz_upload_location, 
            null = True, blank = True)
    class Meta:
        abstract = True

class FakturaPravidelnaPlatba(Platba, Klasifikacia2):
    objednavka_zmluva = models.ForeignKey(ObjednavkaZmluva, 
            null=True, 
            verbose_name = "Objednávka / zmluva",
            on_delete=models.PROTECT, 
            related_name='%(class)s_faktury')    

    # Koho uviesť ako adresata v denniku
    def adresat_text(self):
        return self.objednavka_zmluva.dodavatel.nazov if self.objednavka_zmluva else ""

    def clean(self):
        super(FakturaPravidelnaPlatba, self).clean()

    class Meta:
        abstract = True

class InternyPrevod(Platba, Klasifikacia, GetAdminURL):
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
        if not self.doslo_datum and not self.uhradene_dna: 
            f1 = self._meta.get_field('doslo_datum').verbose_name
            f2 = self._meta.get_field('uhradene_dna').verbose_name
            return f"Prijatá faktúra {self.get_admin_url()} musí mať vyplnené aspoň jedno z polí <em>{f1}</em> alebo <em>{f2}</em>." 
        datum_uhradenia = self.uhradene_dna if self.uhradene_dna else self.doslo_datum
        if datum_uhradenia <zden: return []
        kdatum =  date(zden.year, zden.month+1, zden.day) if zden.month+1 <= 12 else  date(zden.year+1, 1, 1)
        if datum_uhradenia >= kdatum: return []
        platba = {
                "nazov":f"Interný prevod",
                "suma": self.suma,
                "datum": datum_uhradenia,
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
class PrijataFaktura(FakturaPravidelnaPlatba, GetAdminURL):
    oznacenie = "Fa"    #v čísle faktúry, Fa-2021-123
    # Polia
    dcislo = models.CharField("Číslo faktúry dodávateľa", 
            blank=True, 
            null=True,
            max_length=50)
    predmet = models.CharField("Predmet", 
            max_length=100)
    doslo_datum = models.DateField('Došlo dňa',
            null=True)
    sumacm = models.DecimalField("Suma v cudzej mene (s DPH)", 
            help_text = "V prípade uvedenia sumy v cudzej mene vložte do poľa 'Suma' nulu. Pole 'Suma vypňte až bude známa skutočne uhradená suma v EUR",
            max_digits=8, 
            decimal_places=2, 
            blank = True,
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
    prenosDP = models.CharField("Prenos DP", 
            max_length=3, 
            help_text = "Uveďte 'Áno', ak je faktúra v režime prenesenia daňovej povinnosti.",
            default = AnoNie.NIE,
            choices=AnoNie.choices)
    history = HistoricalRecords()

    def clean(self):
        if type(self.objednavka_zmluva) == PrijataFaktura and self.objednavka_zmluva.platna_do and self.splatnost_datum > self.objednavka_zmluva.platna_do:
            raise ValidationError(f"Faktúra nemôže byť vytvorená, lebo zmluva {self.objednavka_zmluva} je platná len do {self.objednavka_zmluva.platna_do}.")
        if self.prenosDP == AnoNie.ANO and self.sadzbadph == SadzbaDPH.P0:
            raise ValidationError(f"Ak je faktúra v režime prenesenia daňovej povinnosti, tak Sadzba DPH nemôže byť 0 %")
        super(PrijataFaktura, self).clean()

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        if not self.dane_na_uhradu and not self.uhradene_dna: 
            f1 = self._meta.get_field('dane_na_uhradu').verbose_name
            f2 = self._meta.get_field('uhradene_dna').verbose_name
            return f"{self._meta.verbose_name} {self.get_admin_url()} musí mať vyplnené aspoň jedno z polí <em>{f1}</em> alebo <em>{f2}</em>." 
        datum_uhradenia = self.uhradene_dna if self.uhradene_dna else self.dane_na_uhradu
        if datum_uhradenia <zden: return []
        kdatum =  date(zden.year, zden.month+1, zden.day) if zden.month+1 <= 12 else  date(zden.year+1, 1, 1)
        if datum_uhradenia >= kdatum: return []
        typ = "zmluva" if type(self.objednavka_zmluva) == Zmluva else "objednávka" if type(self.objednavka_zmluva) == Objednavka else "rozhodnutie" 
        if self.mena != Mena.EUR and not self.suma: 
            suma = float(self.sumacm) / priblizny_kurz[self.mena]
        else:
            suma = float(self.suma)

        #'suma' v prípade prenosu DPH treba rozdeliť na čast bez DPH a DPH, lebo EnÚ odvádza DPH namiesto dodávateľa
        #inak DPH neriešime, lebo EnÚ nie je platcom  DPH
        if self.prenosDP == AnoNie.ANO:
            dph = float(self.sadzbadph)/100
            suma = suma / (1+dph) if self.prenosDP == AnoNie.ANO else suma
        podiel2 = float(self.podiel2)/100. if self.podiel2 else 0
        platby = []
        platba1 = {
                "nazov":f"Faktúra {typ}",
                "suma": round(Decimal(suma*(1-podiel2)),2),
                "datum": datum_uhradenia,
                "cislo": self.cislo,
                "subjekt": self.adresat_text(),
                "zdroj": self.zdroj,
                "zakazka": self.zakazka,
                "ekoklas": self.ekoklas
                }
        platby.append(platba1)
        if podiel2 > 0:
            platba2 = {
                "nazov":f"Faktúra {typ}",
                "suma": round(Decimal(suma*podiel2),2),
                "datum": datum_uhradenia,
                "cislo": self.cislo,
                "subjekt": self.adresat_text(),
                "zdroj": self.zdroj2,
                "zakazka": self.zakazka2,
                "ekoklas": self.ekoklas
                }
            platby.append(platba2)
        if self.prenosDP == AnoNie.ANO:
            dph1 = {
                "nazov":f"DPH prenos DP",
                "suma": round(Decimal(dph*suma*(1-podiel2)),2),
                "datum": datum_uhradenia,
                "cislo": self.cislo,
                "subjekt": self.adresat_text(),
                "zdroj": self.zdroj,
                "zakazka": self.zakazka,
                "ekoklas": EkonomickaKlasifikacia.objects.get(kod="637044")
                }
            platby.append(dph1)
            if podiel2 > 0:
                dph2 = {
                "nazov":f"DPH prenos DP",
                "suma": round(Decimal(dph*suma*podiel2),2),
                "datum": datum_uhradenia,
                "cislo": self.cislo,
                "subjekt": self.adresat_text(),
                "zdroj": self.zdroj2,
                "zakazka": self.zakazka2,
                "ekoklas": EkonomickaKlasifikacia.objects.get(kod="637044")
                }
                platby.append(dph2)


        if self.mena != Mena.EUR and not self.suma: 
            platba["poznamka"] = f"Čerpanie rozpočtu: uhradená suma v EUR faktúry {self.cislo} v cudzej mene je približná. Správnu sumu v EUR vložte do poľa 'Suma' na základe údajov o platbe zo Softipu."
        return platby

    class Meta:
        verbose_name = 'Prijatá faktúra'
        verbose_name_plural = 'Faktúry - Prijaté faktúry'
    def __str__(self):
        return f'Faktúra k "{self.objednavka_zmluva}" : {self.suma} €'

def vystavena_faktura_upload_location(instance, filename):
    return os.path.join(VYSTAVENEFAKTURY_DIR, filename)
class VystavenaFaktura(FakturaPravidelnaPlatba, GetAdminURL):
    oznacenie = "Vf"    #v čísle faktúry, Vf-2021-123
    # Polia
    dcislo = models.CharField("Číslo Softip", 
            help_text = "Zadajte číslo faktúry zo Softipu",
            null=True,
            max_length=50)
    predmet = models.CharField("Predmet", 
            max_length=100)
    doslo_datum = models.DateField('Došlo dňa',
            null=True)
    na_zaklade = models.FileField("Na základe",
            help_text = "Dokument (faktúra od odberateľa), na základe ktorého sa faktúra vystavuje.",
            upload_to=vystavena_faktura_upload_location, 
            null = True)
    zo_softipu = models.FileField("Faktúra zo Softipu",
            help_text = "Faktúra pre odberateľa, vytvorená v Softipe",
            upload_to=vystavena_faktura_upload_location, 
            null = True)
    history = HistoricalRecords()

    def clean(self):
        if type(self.objednavka_zmluva) == PrijataFaktura and self.objednavka_zmluva.platna_do and self.splatnost_datum > self.objednavka_zmluva.platna_do:
            raise ValidationError({'objednavka_zmluva': f"Faktúra nemôže byť vytvorená, lebo zmluva {self.objednavka_zmluva} je platná len do {self.objednavka_zmluva.platna_do}."})
        super(VystavenaFaktura, self).clean()

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        if not self.dane_na_uhradu and not self.uhradene_dna: 
            f1 = self._meta.get_field('dane_na_uhradu').verbose_name
            f2 = self._meta.get_field('uhradene_dna').verbose_name
            return f"{self._meta.verbose_name} {self.get_admin_url()} musí mať vyplnené aspoň jedno z polí <em>{f1}</em> alebo <em>{f2}</em>." 
        datum_uhradenia = self.uhradene_dna if self.uhradene_dna else self.dane_na_uhradu
        if datum_uhradenia <zden: return []
        kdatum =  date(zden.year, zden.month+1, zden.day) if zden.month+1 <= 12 else  date(zden.year+1, 1, 1)
        if datum_uhradenia >= kdatum: return []

        suma = float(self.suma)
        #'suma' treba rozdeliť na sumu bez DPH a DPH
        dph = float(self.sadzbadph)/100
        suma = suma / (1+dph)
        podiel2 = float(self.podiel2)/100. if self.podiel2 else 0
        platby = []
        platba1 = {
                "nazov":f"Vystavená faktúra",
                "suma": round(Decimal(suma*(1-podiel2)),2),
                "datum": datum_uhradenia,
                "cislo": self.cislo,
                "subjekt": self.adresat_text(),
                "zdroj": self.zdroj,
                "zakazka": self.zakazka,
                "ekoklas": self.ekoklas
                }
        platby.append(platba1)
        if podiel2 > 0:
            platba2 = {
                "nazov":f"Vystavená faktúra",
                "suma": round(Decimal(suma*podiel2),2),
                "datum": datum_uhradenia,
                "cislo": self.cislo,
                "subjekt": self.adresat_text(),
                "zdroj": self.zdroj2,
                "zakazka": self.zakazka2,
                "ekoklas": self.ekoklas
                }
            platby.append(platba2)
        if dph > 0:
            dph1 = {
                "nazov":f"DPH vystavená faktúra",
                "suma": round(Decimal(dph*suma*(1-podiel2)),2),
                "datum": datum_uhradenia,
                "cislo": self.cislo,
                "subjekt": self.adresat_text(),
                "zdroj": self.zdroj,
                "zakazka": self.zakazka,
                "ekoklas": EkonomickaKlasifikacia.objects.get(kod="637044")
                }
            platby.append(dph1.copy())
            dph1["suma"] = -dph1["suma"]
            platby.append(dph1.copy())
            if podiel2 > 0:
                dph2 = {
                "nazov":f"DPH vystavená faktúra",
                "suma": round(Decimal(dph*suma*podiel2),2),
                "datum": datum_uhradenia,
                "cislo": self.cislo,
                "subjekt": self.adresat_text(),
                "zdroj": self.zdroj2,
                "zakazka": self.zakazka2,
                "ekoklas": EkonomickaKlasifikacia.objects.get(kod="637044")
                }
                platby.append(dph2.copy())
                dph2["suma"] = -dph2["suma"]
                platby.append(dph2.copy())
        return platby
    

    class Meta:
        verbose_name = 'Vystavená faktúra'
        verbose_name_plural = 'Faktúry - Vystavené faktúry'
    def __str__(self):
        return f'Vystavená faktúra k "{self.objednavka_zmluva}" : {self.suma} €'

class PravidelnaPlatba(FakturaPravidelnaPlatba, GetAdminURL):
    oznacenie = "PP"    #v čísle faktúry, Fa-2021-123
    # Polia
    history = HistoricalRecords()
    typ = models.CharField("Typ platby", 
            max_length=25, 
            choices=TypPP.choices)

    def clean(self):
        super(PravidelnaPlatba, self).clean()

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        if not self.dane_na_uhradu and not self.uhradene_dna and not self.splatnost_datum: 
            f1 = self._meta.get_field('dane_na_uhradu').verbose_name
            f2 = self._meta.get_field('uhradene_dna').verbose_name
            f3 = self._meta.get_field('splatnost_datum').splatnost_datum
            return f"{self._meta.verbose_name} {self.get_admin_url()} musí mať vyplnené aspoň jedno z polí <em>{f1}</em>, <em>{f2}</em> alebo <em>{f3}</em>." 
        if self.uhradene_dna:
            datum_uhradenia = self.uhradene_dna
        elif self.dane_na_uhradu:
            datum_uhradenia = self.dane_na_uhradu
        else:
            datum_uhradenia = self.splatnost_datum
        if datum_uhradenia <zden: return []
        kdatum =  date(zden.year, zden.month+1, zden.day) if zden.month+1 <= 12 else  date(zden.year+1, 1, 1)
        if datum_uhradenia >= kdatum: return []
        nazov = "Faktúra záloha" if self.typ == TypPP.ZALOHA_EL_ENERGIA else ""
        platba = {
                "nazov":nazov,
                "suma": self.suma,
                "datum": datum_uhradenia,
                "subjekt": f"{self.adresat_text()}, (za {zden.year}/{zden.month})", 
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

def najomne_faktura_upload_location(instance, filename):
    return os.path.join(NAJOMNEFAKTURY_DIR, filename)
class NajomneFaktura(Klasifikacia, GetAdminURL):
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
    zo_softipu = models.FileField("Faktúra zo Softipu",
            help_text = "Faktúra pre nájomníka, vytvorená v Softipe",
            upload_to=najomne_faktura_upload_location, 
            null = True)

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
            upload_to=najomne_faktura_upload_location,
            null = True, blank = True)
    history = HistoricalRecords()

    # Koho uviesť ako adresata v denniku
    def adresat_text(self):
        return self.objednavka_zmluva.najomnik.nazov if self.objednavka_zmluva else ""

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        if not self.splatnost_datum:
            f1 = self._meta.get_field('splatnost_datum').verbose_name
            return f"{self._meta.verbose_name} {self.get_admin_url()} musí mať vyplnené  pole <em>{f1}</em>." 
        if self.splatnost_datum <zden: return []
        #if self.splatnost_datum >= date(zden.year, zden.month+1, zden.day): return []
        kdatum =  date(zden.year, zden.month+1, zden.day) if zden.month+1 <= 12 else  date(zden.year+1, 1, 1)
        if self.splatnost_datum >= kdatum: return []
        typ = "prenájom nájomné" if self.typ == TypPN.NAJOMNE else "prenájom služby" if self.typ == TypPN.SLUZBY else "prenájom vyúčtovanie"
        platby =[]
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
        platby.append(platba)
        if self.dan:
            dph = {
                "nazov":f"DPH prenájom",
                "suma": self.dan,
                "datum": self.dane_na_uhradu,
                "subjekt": f"{self.zmluva.najomnik.nazov}, (za {zden.year}/{zden.month})", 
                "cislo": self.cislo,
                "zdroj": self.zdroj,
                "zakazka": self.zakazka,
                "ekoklas": EkonomickaKlasifikacia.objects.get(kod="637044")
                }
            platby.append(dph.copy())
            dph['suma'] = -self.dan
            platby.append(dph.copy())
        return platby
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
            default = 0,
            max_digits=8,
            decimal_places=2,
            null=True)
    za_rok = models.IntegerField("Za rok",
            help_text = "Uveďte rok, ktorého sa dotácia týka")
    history = HistoricalRecords()

    def clean(self):
        #zmeniť číslo položky, ak súvisí s nasledujúcim rokom
        if int(re.findall(r"-(....)-", self.cislo)[0]) != self.za_rok:
            self.cislo = nasledujuce_cislo(RozpoctovaPolozka, self.za_rok)

    #zarátanie dotácií, v roku len raz, v januári
    def cerpanie_rozpoctu(self, zden):
        if not str(zden.year) in self.cislo: return []
        if zden.month != 1: return []
        platba = {
                "nazov":f"Dotácia",
                "cislo": self.cislo,
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
        return f'{self.cislo} ({self.zakazka.kod} - {self.ekoklas.kod} - {self.zdroj.kod})'

class RozpoctovaPolozkaDotacia(Klasifikacia):
    oznacenie = "RPD"
    cislo = models.CharField("Číslo", 
        #help_text = "Číslo rozpočtovej položky. Nová položka za pridáva len vtedy, keď položka s požadovanou klasifikáciou neexistuje.",  
        max_length=50)
    suma = models.DecimalField("Výška dotácie",
            help_text = 'Suma sa pripočíta k zodpovedajúcej rozpočtovej položke za špecifikovaný rok. Ak tá ešte neexistuje, vytvorí sa. <br />Ak ide o zníženie rozpočtu, uveďte <strong>zápornú hodnotu</strong>"',
            max_digits=8,
            decimal_places=2,
            null=True)
    za_rok = models.IntegerField("Za rok")
    rozpoctovapolozka = models.ForeignKey(RozpoctovaPolozka,
            on_delete=models.PROTECT, 
            verbose_name = "Rozpočtová položka",
            null = True,
            related_name='%(class)s_rozpoctovapolozka')  #zabezpečí rozlíšenie modelov, keby dačo
    history = HistoricalRecords()

    def clean(self): 
        #zmeniť číslo položky, ak súvisí s nasledujúcim rokom
        if int(re.findall(r"-(....)-", self.cislo)[0]) != self.za_rok:
            self.cislo = nasledujuce_cislo(RozpoctovaPolozkaDotacia, self.za_rok)
        # pridať súvisiacu rozpočtovú položku (nepodarilo sa RozpoctovaPolozkaDotaciaForm.clean)
        qs = RozpoctovaPolozka.objects.filter(
                za_rok=self.za_rok,
                zdroj=self.zdroj,
                program=self.program,
                zakazka=self.zakazka,
                cinnost=self.cinnost,
                ekoklas=self.ekoklas
            )
        self.rozpoctovapolozka = qs[0]

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
    presun_zdroj = models.ForeignKey(RozpoctovaPolozka,
            on_delete=models.PROTECT, 
            verbose_name = "Z položky",
            null = True,
            related_name='%(class)s_zdroj')  #zabezpečí rozlíšenie modelov, keby dačo
    presun_ciel = models.ForeignKey(RozpoctovaPolozka,
            help_text = 'Ak cieľová rozpočtová položka ešte neexistuje, vytvorte ju s 0-ovou výškou a požadovanou klasifikáciou.',
            on_delete=models.PROTECT, 
            verbose_name = "Do položky",
            null = True,
            related_name='%(class)s_ciel')  #zabezpečí rozlíšenie modelov, keby dačo
    dovod = models.CharField("Dôvod presunu", 
            max_length=200, 
            null=True)
    history = HistoricalRecords()

    def clean(self): 
        rok_zdroj = int(re.findall(r"-(....)-", self.presun_zdroj.cislo)[0])
        rok_ciel = int(re.findall(r"-(....)-", self.presun_ciel.cislo)[0])
        if rok_zdroj != rok_ciel:
            raise ValidationError("Prenos medzi rokmi nie je povolený")
        if self.suma < 0:
            raise ValidationError("Suma musí byť kladná")
        if self.presun_zdroj.suma - self.suma < 0:
            raise ValidationError("Suma na presun prevyšuje sumu zdrojovej položky")

        self.presun_zdroj.suma -= self.suma
        self.presun_ciel.suma += self.suma
        self.presun_zdroj.save()
        self.presun_ciel.save()

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

    za_mesiac = models.CharField("Mesiac", 
            max_length=20, 
            help_text = "Zadajte uplynulý kalendárny mesiac.<br /> <strong>Príspevok na stravné</strong> sa vypočíta na nasledujúci mesiac. Napr. ak koncom mája chcete vytvoriť zoznam príspevkov na jún, zvoľte 'máj'. Vytvorí sa zoznam na jún, v zozname aj bude uvedené 'na jún'.<br /><strong>Zrážka za stravné</strong> sa vypočíta za uplynulý mesiac.",
            null = True,
            choices=Mesiace.choices)

    typ_zoznamu = models.CharField("Typ zoznamu",
            max_length=20,
            help_text = "Zvoľte typ zoznamu.<br/>Položku uložte a následne akciou 'Generovať zoznam príspevkov/zrážok' vytvorte súbor so zoznamom.",
            null = True,
            choices=Stravne.choices)

    datum_odoslania = models.DateField('Dátum odoslania',
            help_text = "Zadajte dátum odoslania tabuľky so zoznamom. Po zadaní dátumu sa vytvorí záznam v Denníku prijatej a odoslanej pošty",
            blank=True, null=True)

    suma_zamestnavatel = models.DecimalField("Príspevok (zrážka) zamestnávateľ", 
            help_text = "Príspevok zamestnávateľa (Ek. klas. 642014) na stravné.<br />Ak ide o vyplatenie zamestnancovi, uveďte zápornú hodnotu, ak ide o zrážku, tak kladnú hodnotu.<br />Suma sa automaticky generuje akciou 'Generovať zoznam príspevkov/zrážok'",
            max_digits=8, 
            decimal_places=2, 
            null = True,
            blank=True,
            default=0)

    # Položka suma_socfond nemá Ek. klasifikáciu, soc. fond nie sú peniaze EnÚ
    suma_socfond = models.DecimalField("Príspevok (zrážka) soc. fond", 
            help_text = "Príspevok zo sociálneho fondu (Ek. klas. 642014) na stravné.<br />Ak ide o vyplatenie zamestnancovi, uveďte zápornú hodnotu, ak ide o zrážku, tak kladnú hodnotu.<br />Vytvorením Príspevku na stravné sa automaticky vytvorí položka sociálneho fondu. <br /> Suma sa automaticky generuje akciou 'Generovať zoznam príspevkov/zrážok'",
            max_digits=8, 
            decimal_places=2, 
            null = True,
            blank=True,
            default=0)
    po_zamestnancoch = models.FileField("Prehľad po zamestnancoch",
            help_text = "Súbor s mesačným prehľadom príspevkov na stravné po zamestnancoch",
            upload_to=prispevok_stravne_upload_location, 
            null = True,
            blank=True)
    history = HistoricalRecords()

    # test platnosti dát
    def clean(self): 
        if self.suma_zamestnavatel * self.suma_socfond < 0:
            raise ValidationError("Položky 'Príspevok zamestnávateľa' a 'Príspevok zo soc. fondu' musia byť buď len kladné alebo len záporné.")
        if not self.suma_zamestnavatel or not self.suma_socfond: self.aktualizovat_SF

    #vytvoriť alebo aktualizovať súvisiacu položku v účte SF
    def aktualizovat_SF(self):
        qs = SocialnyFond.objects.filter(predmet__startswith = self.cislo)
        if not qs:
            sf = SocialnyFond(
                cislo = nasledujuce_cislo(SocialnyFond),
                suma = self.suma_socfond,
                datum_platby = date.today(),
                predmet = f'{self.cislo} - {"príspevok na stravné" if self.typ_zoznamu==Stravne.PRISPEVKY else "zrážka za stravné"} za {Mesiace(self.za_mesiac).label}'
            )
        else:
            sf = qs[0]
            sf.datum_platby = date.today()
            sf.suma = self.suma_socfond
        sf.save()
        return sf.id, sf.cislo

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    #V starších pdf s príspevkami (do 08/2023) je v hlavičke nesprávny údaj o mesiaci, ktorého sa príspevok týka.
    #V tom prípade sa mesiac zadáva na základe dátumu vytvorenia dokumentu dolu pod tabuľkou
    def cerpanie_rozpoctu(self, zden):
        if not self.za_mesiac: return []    #pole nie je vyplnené
        if not str(zden.year) in self.cislo: return []  #nesprávny rok
        if zden.month != mesiace_num[self.za_mesiac][0]: return [] #nesprávny mesiac 
        platby = []
        if self.suma_zamestnavatel < 0:
            platba = {
                "nazov":"Stravné príspevok",
                "suma": self.suma_zamestnavatel,
                "socfond": self.suma_socfond,
                "datum": zden,
                "subjekt": "Zamestnanci",
                "osoba": "Zamestnanci",
                "cislo": self.cislo,
                "zdroj": self.zdroj,
                "zakazka": self.zakazka,
                "ekoklas": self.ekoklas
                }
            platby.append(platba)
        else:
            platba = {
                "nazov":"Stravné zrážky",
                "suma": self.suma_zamestnavatel,
                "socfond": self.suma_socfond,
                "datum": zden,
                "subjekt": "Zamestnanci",
                "osoba": "Zamestnanci",
                "cislo": self.cislo,
                "zdroj": self.zdroj,
                "zakazka": self.zakazka,
                "ekoklas": self.ekoklas
                }
            platby.append(platba)
        return platby

    class Meta:
        verbose_name = 'Príspevok na stravné / zrážka za stravné'
        verbose_name_plural = 'PaM - Stravné'
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

    def priezviskomeno(self, oddelovac=""):
        return f"{self.priezvisko}{oddelovac}{self.meno}"

    def menopriezvisko(self, titul=False):
        titul_pred = f"{self.titul_pred_menom} " if titul and self.titul_pred_menom else ""
        titul_za = f", {self.titul_za_menom} " if titul and self.titul_za_menom else ""
        return f"{titul_pred}{self.meno} {self.priezvisko}{titul_za}"

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
    cislo_zamestnanca = models.CharField("ČísloZam", 
            null = True,
            max_length=50)
    cislo_biometric = models.IntegerField("ČísloBiom", 
            help_text = "Uveďte číslo zamestnanca v Biometricu",
            null = True)
    zamestnanie_od = models.DateField('1. zamestnanie od',
            help_text = "Dátum nástupu do 1. zamestnania. Preberá sa zo Softipu, kde sa vypočíta z dátumu nástupu do EnÚ a započítanej praxe",
            blank=True,
            null=True)
    stupnica = models.CharField("Platová stupnica",
            max_length=10, 
            help_text = "Uveďte typ stupnice platovej tarify zamestnanca",
            null = True,
            choices=PlatovaStupnica.choices,
            default=PlatovaStupnica.OSOBITNA
            )
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
    bez_stravneho = models.TextField('Bez stravného od / do',
            help_text = "Zadajte obdobie, v ktorom sa zamestnancovi z dôvodu dlhej neprítomnosti (materská, PN, NV) <strong>nemá vyplácať</strong> príspevok na stravné. <br />Obdobie zadajte ako <em>prvy_den_v_prvom_mesiaci, posledny_den_v_poslednom_mesiaci</em>, napr. <em>1.2.2022, 31.8.2022</em>. Ak druhý dátum nie je známy, tak ho neuveďte.<br />Prvý dátum treba zadať pred výpočtom príspevku za mesiac, v ktorom sa príspevok nemá vyplatiť.<br />Príspevok sa v danom mesiaci nevyplatí len vtedy, ak neprítomnosť zadaná v PaM - Neprítomnosť trvá celý tento mesiac (napr. neukončená PN, MD alebo NV na celý mesiac. <br />Za dátumami možno zadať poznámku, v ktorej sa nenachádza dátum.)",
            blank=True,
            null=True)
    history = HistoricalRecords()

    def clean(self): 
        pocet_datumov=[] #Neukončený môže byť len jeden, a to posledný mesiac
        datumy1 = []    #kontrola poradia
        for nn, riadok in enumerate(self.bez_stravneho.split("\r\n")):
            if not riadok: continue
            datumy = re.findall("([0-9]*[.][0-9]*[.][0-9]{4})", riadok)
            if len(datumy) == 0:
                raise ValidationError({"bez_stravneho": f"Na riadku {nn+1} nebol nájdený žiaden dátum v tvare 'DD.MM.RRRR'."})
            elif len(datumy) > 2:
                 raise ValidationError({"bez_stravneho": f"Na riadku {nn+1} sa nachádzajú viac ako dva dátumy."})
            else:
                try:
                    datum1 = datetime.strptime(datumy[0], "%d.%m.%Y")
                except:
                    raise ValidationError({"bez_stravneho": f"Prvý dátum {datumy[0]} na riadku {nn+1} nie je v tvare 'DD.MM.RRRR' alebo ide o neexistujúci dátum."})
                if datum1.day != 1:
                    raise ValidationError({"bez_stravneho": f"Prvý dátum  {datumy[0]} na riadku {nn+1} nie je prvý deň v mesiaci alebo nie je v tvare 'DD.MM.RRRR."})
                if len(datumy) == 2:
                    try:
                        datum2 = datetime.strptime(datumy[1], "%d.%m.%Y")
                    except:
                        raise ValidationError({"bez_stravneho": f"Druhý dátum {datumy[1]} na riadku {nn+1} nie je v tvare 'DD.MM.RRRR' alebo ide o neexistujúci dátum."})
                    if (datum2 + timedelta(days=1)).day != 1:  # 1. deň nasl. mesiaca
                        raise ValidationError({"bez_stravneho": f"Druhý dátum {datumy[1]} na riadku {nn+1} nie je posledný deň v mesiaci  alebo nie je v tvare 'DD.MM.RRRR."})
                    if datum2 < datum1:
                        raise ValidationError({"bez_stravneho": f"Dátumy na riadku {nn+1} nie sú v správnom poradí od,do."})
            pocet_datumov.append(len(datumy))
            datumy1.append(datum1)
        jeden_datum = [1 if nn==1 else 0 for nn in pocet_datumov]
        if sum(jeden_datum) > 1:
            raise ValidationError({"bez_stravneho": f"Len jeden mesiac môže byť neukončený (posledný v zozname)."})
        if sum(jeden_datum) == 1 and jeden_datum[-1] != 1:
            raise ValidationError({"bez_stravneho": f"Neukončený môže byť len posledný mesiac v zozname."})
        if len(datumy1) > 1:
            for d1,d2 in zip(datumy1[:-1], datumy1[1:]):
                if d2 < d1:
                    raise ValidationError({"bez_stravneho": f"Riadky {d1.strftime('%d.%m.%Y')} a {d2.strftime('%d.%m.%Y')} sú v nesprávnom poradí."})

        pass

    #Či vyplatiť príspevok na stravné za mesiac, ktorý začína zden
    def nevyplacat_stravne(self, zden):
        if not self.bez_stravneho: return False
        for riadok in self.bez_stravneho.split("\r\n"):
            if not riadok: continue
            datumy = re.findall("([0-9]*[.][0-9]*[.][0-9]{4})", riadok)
            if len(datumy) == 1:
                datum1 = datetime.strptime(datumy[0], "%d.%m.%Y")
                #Porovnávame len 1. deň v mesiaci
                if datum1.date() <= zden:
                    return True
            else:
                datum1 = datetime.strptime(datumy[0], "%d.%m.%Y")
                datum2 = datetime.strptime(datumy[1], "%d.%m.%Y")
                #Porovnávame len 1. deň v mesiaci
                if datum1.date() <= zden and zden < datum2.date():
                    return True
        return False

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
    oznacenie = "PV"
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

    #Konverzia typu dochodku na pozadovany typ vo funkcii ZamestnanecOdvody
    @staticmethod
    def td_konv(osoba, zden):
        if osoba.poberatel_doch == AnoNie.ANO and osoba.datum_doch <= zden:
            td = osoba.typ_doch
            return "InvDoch30" if td==TypDochodku.INVALIDNY30 else "InvDoch70" if td== TypDochodku.INVALIDNY70 else "StarDoch" if td==TypDochodku.STAROBNY else "VyslDoch" if td==TypDochodku.INVAL_VYSL else "Bezny"
        else:
            return "Bezny"

    def duplikovat(self):
        novy = PlatovyVymer.objects.create(
                cislo_zamestnanca = self.cislo_zamestnanca,
                zamestnanec = self.zamestnanec,
                tarifny_plat = self.tarifny_plat,
                osobny_priplatok = self.osobny_priplatok,
                funkcny_priplatok = self.funkcny_priplatok,
                platova_trieda = self.platova_trieda,
                platovy_stupen = self.platovy_stupen,
                uvazok = self.uvazok,
                uvazok_denne = self.uvazok_denne,
                program = Program.objects.get(id=4),    #nealokovaný
                ekoklas = self.ekoklas,
                zakazka = self.zakazka,
                zdroj = self.zdroj
            )
        return novy

    #vypočíta počet dní neprítomnosti vo viacerých kategóriách
    def nepritomnost_za_mesiac(self, zden, pre_stravne=False):
        if zden < self.datum_od: return []
        if self.datum_do and zden > self.datum_do: return []

        #zobrať do úvahy neprítomnosť za daný mesiac
        qs = Nepritomnost.objects.filter(zamestnanec=self.zamestnanec)
        qs1 = qs.exclude(nepritomnost_do__lt=zden)  # vylúčiť nevyhovujúce
        next_month = zden + relativedelta(months=1, day=1)  # 1. deň nasl. mesiaca
        qs2 = qs1.exclude(nepritomnost_od__gte=next_month)  # vylúčiť nevyhovujúce

        ddov = 0         #počet dní dovolenky. Za všetky sa platí náhrada mzdy vo výške platu
        ddov2 = 0        #počet poldní dovolenky.
        dosob = 0        #Počet dní osobných prekážok v práci (lekár a podobne). Platí sa náhrada mzdy vo výške platu 
        dnepl = 0        #neplatené dni. Materská, PN a neplatené voľno. Náhrada za PN sa ráta inak
        dpn1 = 0         #počet dní práceneschopnosti v dňoch 1-3. Platí sa náhrada 55 %
        dpn2 = 0         #počet dní práceneschopnosti v dňoch 4-10. Platí sa náhrada 80 %
        docr = 0         #Počet dní OČR

        pdni = int(self.uvazok/self.uvazok_denne)    #počet pracovných dní v týždni, napr. 18.85/6.25=3
        for nn in qs2:  #môže byť viac neprítomností za mesiac
            try:
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
                    #Stravné: pri poldni dovolenky sa nevypláca
                    ddov2 += 1
                elif nn.nepritomnost_typ == TypNepritomnosti.DOVOLENKA:
                    ddov += prac_dni(prvy,posledny, pdni, zahrnut_sviatky=False)    #Sviatky sa nezarátajú do dovolenky, ale ako bežný prac. deň
                elif nn.nepritomnost_typ == TypNepritomnosti.PN:
                    if pre_stravne:
                        dnepl += prac_dni(prvy,posledny, pdni, zahrnut_sviatky=False)
                    else:
                        dnepl += prac_dni(prvy,posledny, pdni, zahrnut_sviatky=True)    #Sviatky sa do PN zarátajú, náhrada sa ráta inak
                    #Prvé 3 dni, 55%
                    dpn1 += prekryv_dni(zden, nn.nepritomnost_od, nn.nepritomnost_od+timedelta(days=2))
                    #Dni 4 až 10, 80%
                    dpn2 += prekryv_dni(zden, nn.nepritomnost_od+timedelta(days=3), min(nn.nepritomnost_od+timedelta(days=9), posledny))
                elif nn.nepritomnost_typ in [TypNepritomnosti.OCR]:
                    docr += prac_dni(prvy,posledny, pdni, zahrnut_sviatky=True)    #Sviatky sa zarátajú, nie sú platené
                elif nn.nepritomnost_typ in [TypNepritomnosti.MATERSKA, TypNepritomnosti.NEPLATENE]:
                    if pre_stravne:
                        dnepl += prac_dni(prvy,posledny, pdni, zahrnut_sviatky=False)    #Sviatky sa zarátajú, nie sú platené
                    else:
                        dnepl += prac_dni(prvy,posledny, pdni, zahrnut_sviatky=True)    #Sviatky sa zarátajú, nie sú platené
                elif nn.nepritomnost_typ in [TypNepritomnosti.LEKARDOPROVOD, TypNepritomnosti.LEKAR]:
                    dlzka_nepritomnosti = nn.dlzka_nepritomnosti if nn.dlzka_nepritomnosti else self.uvazok_denne
                    dosob_hod = float(dlzka_nepritomnosti*prac_dni(prvy,posledny, pdni, zahrnut_sviatky=True)/self.uvazok_denne)    #Osobné prekážky vo sviatok sa nemajú čo vyskytovať
                    if pre_stravne:
                        #Stravné: vypláca sa, len keď osoba pracuje viac ako STRAVNE_HOD
                        dosob_hod = 1 if self.uvazok_denne*Decimal(dosob_hod) > self.uvazok_denne - STRAVNE_HOD else 0
                    dosob += dosob_hod
                elif nn.nepritomnost_typ in [TypNepritomnosti.SLUZOBNA, TypNepritomnosti.PRACADOMA, TypNepritomnosti.SKOLENIE]:
                    pass    #normálna mzda
                else:   #Osobné prekážky (Pracovné voľno)
                    dosob += prac_dni(prvy,posledny, pdni, zahrnut_sviatky=True)    #Osobné prekážky vo sviatok sa nemajú čo vyskytovať
            except TypeError:
                raise TypeError(f"Chyba pri spracovaní platového výmeru '{self}', neprítomnosť '{nn}'")

        return [pdni, ddov, ddov2, dosob, dnepl, dpn1, dpn2, docr]

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    #Mzdy sa vyplácajú spätne, t.j. v máji sa vypláca mzda za apríl
    #Decembrová výplata sa vypláca už v decembri, v decembri teda zamestnanec dostane výplatu dvakrát, v januári výplatu nedostane
    #Spôsob výpočtu bol skontrolovaný z hľadiska zaťažovanie rozpočtu aj z hľadiska mzdovej rekapitulácie.
    def cerpanie_rozpoctu(self, zden):
        if zden < self.datum_od: return []
        if self.datum_do and zden > self.datum_do: return []

        nepritomnost = self.nepritomnost_za_mesiac(zden)
        if not nepritomnost: return []
        pdni, ddov, ddov2, dosob, dnepl, dpn1, dpn2, docr = nepritomnost
        #Pridať OČR k neplateným, tu sa rátajú spolu
        dnepl += docr
        #Pripočítať poldni dovolenky
        ddov += ddov2/2

        #if zden == date(2022,7,1) and self.zamestnanec.meno=="Helena":
            #print(self.zamestnanec.priezvisko, ddov, dosob, dnepl, dpn1, dpn2)
            #trace()
            #pass
        #Počet pracovných dní
        #pri častočnom úväzku len približné, na presný výpočet by sme asi potrebovali vedieť, v ktorých dňoch zamestnanec pracuje.
        #Tento údaj nie je ani v Softipe
        dprac = prac_dni(zden, ppd=pdni, zahrnut_sviatky=False) #Sviatky sa rátajú ako pracovné dni

        koef_prac = 1 - float(ddov+dosob+dnepl) / dprac    #Koeficient odpracovaných dní
        koef_osob = dosob / dprac
        koef_dov = float(ddov / dprac)    #počet prac dní v rámci dovolenky / počet prac. dní v mesiaci

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
                "osoba": self.zamestnanec,
                "suma": -round(Decimal(koef_prac*float(self.tarifny_plat)),2),
                "zdroj": zdroj,
                "zakazka": zakazka,
                "datum": zden if zden < date.today() else None,
                "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}",
                "cislo": self.cislo if self.cislo else "-",
                "ekoklas": self.ekoklas
                }
        osobny = {
                "nazov": "Plat osobný príplatok",
                "osoba": self.zamestnanec,
                "suma": -round(Decimal(koef_prac*float(self.osobny_priplatok)),2),
                "zdroj": zdroj,
                "zakazka": zakazka,
                "datum": zden if zden < date.today() else None,
                "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}",
                "cislo": self.cislo if self.cislo else "-",
                "ekoklas": EkonomickaKlasifikacia.objects.get(kod="612001")
                }
        funkcny = {
                "nazov": "Plat príplatok za riadenie",
                "osoba": self.zamestnanec,
                "suma": -round(Decimal(koef_prac*float(self.funkcny_priplatok)),2),
                "zdroj": zdroj,
                "zakazka": zakazka,
                "datum": zden if zden < date.today() else None,
                "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}",
                "cislo": self.cislo if self.cislo else "-",
                "ekoklas": EkonomickaKlasifikacia.objects.get(kod="612002")
                }
        tabulkovy_plat = float(self.tarifny_plat) + float(self.osobny_priplatok) + float(self.funkcny_priplatok)

        #PN
        nahrada_pn = None
        if dpn1 or dpn2:
            denny_vz, text_vz = self.urcit_VZ(zden)
            nahrada_pn = {
                    "nazov": "Náhrada mzdy - PN",
                    "suma": -round(Decimal((dpn1*PN1(zden)+dpn2*PN2(zden))*denny_vz/100),2),
                    "zdroj": zdroj,
                    "zakazka": zakazka,
                    "datum": zden if zden < date.today() else None,
                    "osoba": self.zamestnanec,
                    "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}",
                    "cislo": self.cislo if self.cislo else "-",
                    "ekoklas": EkonomickaKlasifikacia.objects.get(kod="642015")
                    }
            if text_vz and "približne" in text_vz:
                nahrada_pn["poznamka"] = f"Čerpanie rozpočtu: vypočítaná suma náhrad PN je približná. V údajoch zamestnanca '{self.zamestnanec}' treba na základe údajov v Softipe doplniť denný vymeriavací základ za mesiac {zden.year}/{zden.month}."

        #Osobné prekážky
        nahrada_osob = None
        if dosob:
            nahrada_osob = {
                    "nazov": "Náhrada mzdy - osobné prekážky",
                    "suma": -round(Decimal(tabulkovy_plat*koef_osob),2),
                    "zdroj": zdroj,
                    "zakazka": zakazka,
                    "datum": zden if zden < date.today() else None,
                    "osoba": self.zamestnanec,
                    "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}",
                    "cislo": self.cislo if self.cislo else "-",
                    "ekoklas": EkonomickaKlasifikacia.objects.get(kod="611")    #Overené
                    }

        nahrada_dov = None
        if ddov:
            nahrada_dov = {
                    "nazov": "Náhrada mzdy - dovolenka",
                    "suma": -round(Decimal(koef_dov*tabulkovy_plat),2),
                    "zdroj": zdroj,
                    "zakazka": zakazka,
                    "datum": zden if zden < date.today() else None,
                    "osoba": self.zamestnanec,
                    "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}",
                    "cislo": self.cislo if self.cislo else "-",
                    "ekoklas": EkonomickaKlasifikacia.objects.get(kod="611")
                    }

        retlist = [tarifny, osobny, funkcny]
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

def nepritomnost_upload_location(instance, filename):
    return os.path.join(NEPRITOMNOST_DIR, filename)
class Nepritomnost(models.Model):
    oznacenie = "Np"
    cislo = models.CharField("Číslo", 
            #help_text: definovaný vo forms
            null = True,
            max_length=50)
    subor_nepritomnost = models.FileField("Import. súbor",
            help_text = "XLSX súbor so zoznamom neprítomností.<br />Po vložení treba akciou 'Generovať záznamy neprítomnosti' vytvoriť jednotlivé záznamy.",
            upload_to=nepritomnost_upload_location,
            blank=True, 
            null=True
            )
    subor_nepritomnost_exp = models.FileField("Export. súbor",
            help_text = "XLSX súbor so zoznamom neprítomností pre učtáreň.<br />Súbor sa vytvára akciou 'Exportovať neprítomnosť pre učtáreň', tak že sa zvolí riadok kde je importovaný súbor, a to za rovnaký mesiac.<br />Súbor sa vytvára z jednotlivých položiek neprítomnosti, nie z dát v importovanom súbore.",
            upload_to=nepritomnost_upload_location,
            blank=True,
            null=True
            )
    poznamka = models.CharField("Poznámka", 
            max_length=60,
            blank = True,
            null=True
            )
    datum_odoslania = models.DateField('Dátum odoslania',
            help_text = "Zadajte dátum odoslania tabuľky so zoznamom neprítomností. Po zadaní dátumu sa vytvorí záznam v Denníku prijatej a odoslanej pošty",
            blank=True, null=True)
    zamestnanec = models.ForeignKey(Zamestnanec,
            on_delete=models.PROTECT, 
            verbose_name = "Zamestnanec",
            related_name='%(class)s_zamestnanec',  #zabezpečí rozlíšenie modelov, keby dačo
            blank=True, 
            null=True
            )
    nepritomnost_od= models.DateField('Neprítomnosť od',
            help_text = 'Prvý deň neprítomnosti',
            blank=True, 
            null=True)
    nepritomnost_do= models.DateField('Neprítomnosť do',
            help_text = 'Posledný deň neprítomnosti',
            blank=True, 
            null=True)
    nepritomnost_typ = models.CharField("Typ neprítomnosti",
            max_length=20, 
            blank=True, 
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
        if self.nepritomnost_od:
            od = self.nepritomnost_od.strftime('%d. %m. %Y')
            return f"{self.zamestnanec.priezvisko} od {od}"
        else:
            return "Neprítomnosť - súbor"

    def clean(self): 
        errors={}
        if self.zamestnanec and self.nepritomnost_typ != TypNepritomnosti.PN and not self.nepritomnost_do:
            errors['nepritomnost_do'] ="Neprítomnosť musí byť ukončená (okrem PN)."
            raise ValidationError(errors)
        if self.nepritomnost_typ in [TypNepritomnosti.LEKAR, TypNepritomnosti.LEKARDOPROVOD]:
            if self.nepritomnost_do - self.nepritomnost_od > timedelta(0): 
                errors['nepritomnost_do'] ="Neprítomnosť v prípade návštevy u lekára alebo doprovodu k lekárovi možno zadať len na jeden deň."
                raise ValidationError(errors)

def odmena_upload_location(instance, filename):
    return os.path.join(ODMENY_DIR, filename)
class OdmenaOprava(Klasifikacia):
    oznacenie = "OO"
    cislo = models.CharField("Číslo", 
            #help_text: definovaný vo forms
            null = True,
            max_length=50)
    typ = models.CharField("Typ záznamu",
            max_length=20, 
            help_text = "Uveďte, či ide o odmenu, súbor s odmenami alebo opravu vyplatenej mzdy",
            null = True,
            choices=OdmenaAleboOprava.choices)
    zamestnanec = models.ForeignKey(Zamestnanec,
            help_text = "Nevypĺňa sa, ak sa vkladá súbor so zoznamom odmien",
            on_delete=models.PROTECT, 
            verbose_name = "Zamestnanec",
            related_name='%(class)s_zamestnanec',  #zabezpečí rozlíšenie modelov, keby dačo
            blank=True, 
            null=True
            )
    subor_odmeny = models.FileField("Súbor so zoznamom odmien alebo dôvodom",
            help_text = "XLSX súbor so zoznamom odmien.<br />Po vygenerovaní krycieho listu sa vytvoria záznamy jednotlivo pre všetkých odmenených. Ak sa záznam s takýmto súborom zmaže,tak sa zmažú aj všetky s ním súvisiace záznamy. <br />Dôvod (napr. udelenie odmeny P sav) prikladať ako PDF súbor.",
            upload_to=odmena_upload_location,
            blank=True, 
            null=True
            )
    suma = models.DecimalField("Suma", 
            help_text = "Výška odmeny alebo opravy. Odmena je záporná, oprava môže byť kladná (t.j. zmestnancovi bola strhnutá z výplaty).<br /> Ak sa vkladá súbor so zoznamom odmien, uveďte súčet.",
            max_digits=8, 
            decimal_places=2, 
            null=True,
            default=0)
    vyplatene_v_obdobi = models.CharField("Vyplatené v", 
            help_text = "Uveďte mesiac vyplatenia odmeny alebo mesiac, ku ktorému sa oprava vzťahuje v tvare <em>MM/RRRR</em>", 
            null = True,
            max_length=10)
    zdovodnenie = models.TextField("Zdôvodnenie", 
            help_text = "Zadajte dôvod vyplatenia odmeny alebo vykonania opravy. <br />Začnite 'za' a text neukončite bodkou",
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
        errors={}
        if self.typ == OdmenaAleboOprava.ODMENA and not self.zamestnanec:
            errors["zamestnanec"] = "Pole 'Zamestnanec' nebolo vyplnené."
        if self.typ == OdmenaAleboOprava.ODMENAS.value and not self.subor_odmeny:
            errors["subor_odmeny"] = "Pole 'Súbor so zozmamom odmien' nebolo vyplnené."
        if self.typ in [OdmenaAleboOprava.ODMENA, OdmenaAleboOprava.ODMENAS, OdmenaAleboOprava.ODCHODNE, OdmenaAleboOprava.ODSTUPNE] and self.suma >= 0:
            errors["suma"] = "Suma odmeny, odchodného a odstupného musí byť záporná"
        if self.vyplatene_v_obdobi:
            if not OdmenaOprava.check_vyplatene_v(self.vyplatene_v_obdobi):
                errors["vyplatene_v_obdobi"] = "Údaj v poli 'Vyplatené v' musí byť v tvare MM/RRRR (napr. 07/2022)"
        if self.typ == OdmenaAleboOprava.ODMENAS.value and self.subor_odmeny:
            if not self.subor_odmeny.name.split(".")[-1] in ["xlsx"]:
                errors["subor_odmeny"] = "Súbor so zoznamom odmien musí byť vo formáte xlsx"
        elif self.subor_odmeny:
            if not self.subor_odmeny.name.split(".")[-1] in ["pdf", "PDF"]:
                errors["subor_odmeny"] = "Súbor s dôvodom musí byť vo formáte pdf."
        if errors:
            raise ValidationError(errors)

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        if self.vyplatene_v_obdobi != "%02d/%d"%(zden.month, zden.year): return []
        if self.typ == OdmenaAleboOprava.ODMENAS: return []

        platby = []
        podnazov = ""
        if self.typ == OdmenaAleboOprava.ODMENA:
            nazov = "Plat odmena"
        elif self.typ == OdmenaAleboOprava.OPRAVATARIF:
            nazov = "Plat tarifný plat"
        elif self.typ == OdmenaAleboOprava.ODCHODNE:
            nazov = "Plat odchodné"
        elif self.typ == OdmenaAleboOprava.ODSTUPNE:
            nazov = "Plat odstupné"
        elif self.typ == OdmenaAleboOprava.OPRAVAOSOB:
            nazov = "Plat osobný príplatok"
        elif self.typ == OdmenaAleboOprava.OPRAVARIAD:
            nazov = "Plat príplatok za riadenie"
        elif self.typ == OdmenaAleboOprava.DOVOLENKA:
            nazov = "Náhrada mzdy - dovolenka"
        elif self.typ == OdmenaAleboOprava.OPRAVAZR:
            # Podľa admin.gen_soczdrav
            nazov = f"Sociálne poistné {self.ekoklas.kod}"
            podnazov = "Plat poistenie sociálne"

        platba = {
            "nazov": nazov,
            "osoba": self.zamestnanec,
            "suma": self.suma,
            "datum": zden,
            "osoba": self.zamestnanec,
            "subjekt": f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}", 
            "cislo": self.cislo,
            "zdroj": self.zdroj,
            "zakazka": self.zakazka,
            "ekoklas": self.ekoklas
            }
        if podnazov: platba["podnazov"] = podnazov
        platby.append(platba)
        return platby

    class Meta:
        verbose_name = "Odmena alebo oprava"
        verbose_name_plural = "PaM - Odmeny a opravy"
    def __str__(self):
        subjekt = "Súbor so zoznamom odnmien" if self.typ == OdmenaAleboOprava.ODMENAS else f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}"
        return f"{self.typ} {subjekt}"

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
    datum_podpisu_ziadosti = models.DateField('Dátum podpisu žiadosti',
            help_text = "Dátum podpisu žiadosti vedením. <br />Po zadaní sa vytvorí záznam v denníku na odoslanie žiadosti na PaM",
            null=True
            )
    subor_vyuctovanie = models.FileField("Vyúčtovanie príspevku",
            help_text = "Súbor s vyúčtovaním príspevku.<br />Po zadaní sa vytvorí záznam v Denníku.",
            upload_to=rekreacia_upload_location,
            blank=True, 
            null=True
            )
    prispevok = models.DecimalField("Na vyplatenie", 
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
    history = HistoricalRecords()

    @staticmethod
    def check_vyplatene_v(value):
        return re.findall(r"[0-9][0-9]/[0-9][0-9][0-9][0-9]", value)


    def clean(self): 
        if (self.prispevok or self.subor_vyuctovanie or self.vyplatene_v_obdobi) and  not (self.prispevok and self.subor_vyuctovanie and self.vyplatene_v_obdobi):
            raise ValidationError("Vyplniť treba všetky tri polia 'Vyúčtovanie príspevku', 'Na vyplatenie' a 'Vyplatené v'")
        if self.prispevok and self.prispevok > 0:
            raise ValidationError("Suma 'Na vyplatenie' musí byť záporná")
        if self.vyplatene_v_obdobi and not PrispevokNaRekreaciu.check_vyplatene_v(self.vyplatene_v_obdobi):
            self.vyplatene_v_obdobi = None
            raise ValidationError("Údaj v poli 'Vyplatené v' musí byť v tvare MM/RRRR (napr. 07/2022)")

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        zobdobie = "%02d/%d"%(zden.month,zden.year)
        if zobdobie != self.vyplatene_v_obdobi: return []
        platba = {
                "nazov": "Príspevok na rekreáciu",
                "suma": self.prispevok,
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
        return f"{self.zamestnanec.priezvisko}, {self.zamestnanec.meno}"

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
            help_text = "Uveďte 'Áno', ak si dohodár (dôchodca) na túto dohodu uplatňuje odvodovú výnimku",
            null = True,
            choices=AnoNie.choices)
    predmet = models.TextField("Pracovná činnosť", 
            help_text = "Zadajte stručný popis práce (max. 250 znakov, 3 riadky)",
            max_length=500,
            null=True)
    miesto_vykonu = models.CharField("Miesto výkonu", 
            max_length=200, 
            help_text = "Miesto výkonu práce: presná adresa alebo presné adresy, prípadne ak je viac adries, určenie hlavného miesta výkonu práce, <br />alebo znenie: <strong>miesto výkonu práce určuje zamestnanec</strong>",
            null = True)
    pracovny_cas = models.CharField("Pracovný čas", 
            max_length=200, 
            help_text = 'Uviesť jednu z možností:<ul><li>1. znenie: "<strong>zamestnanec si sám rozvrhuje pracovný čas</strong></li> <li>2. znenie: uviesť presnú informáciu o <ul><li>a) dňoch a časových úsekoch, v ktorých môže od zamestnanca vyžadovať vykonávanie práce,</li> <li>b) lehote, v ktorej má byť zamestnanec informovaný o výkone práce pred jej začiatkom, ktorá nesmie byť kratšia ako 24 hodín.</li> </ul> </li></ul>',
            null = True)
    datum_od = models.DateField('Dátum od',
            help_text = "Zadajte dátum začiatku platnosti dohody",
            null=True)
    datum_do = models.DateField('Dátum do',
            help_text = "Zadajte dátum konca platnosti dohody",
            null=True)
    pomocnik = models.CharField("Pomoc rod. príslušníkov", 
            help_text = "Uveďte zoznam rod. príslušníkov, ktorí budú pomáhať pri vykonávaní činnosti, alebo nechajte prázdne. Pre každého uveďte meno a priezvisko.",
            null = True, blank = True,
            max_length=100)
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
    def adresat_text(self):
        return self.zmluvna_strana

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
    interny_prevod = models.CharField("Int. prevod", 
            max_length=3, 
            help_text = "Uveďte 'Áno', ak sa hradí interným prevodom na organizačnú zložku. Takáto položka sa nezaráta do platovej rekapitulácie",
            null = True,
            default = AnoNie.NIE,
            choices=AnoNie.choices)
    id_tsh = models.CharField("Číslo priradené THS",
            help_text = "Uveďte číslo, pod ktorým dohody vedie THS",
            null = True, blank = True,
            max_length=100)
    datum_ukoncenia = models.DateField('Dátum ukončenia',
            help_text = "Zadajte dátum predčasného ukončenia platnosti dohody",
            blank = True,
            null=True)
    vyplatena_odmena = models.DecimalField("Vyplatená odmena",
            help_text = "Zadajte sumu na vyplatenie. Ak ponecháte 0, doplní sa suma z poľa 'Celková suma v EUR'<br /><strong>Vyplniť v prípade predčasnéo ukončenia</strong> dohody.",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    history = HistoricalRecords()

    #Konverzia typu dochodku na pozadovany typ vo funkcii DohodarOdvody
    @staticmethod
    def td_konv(osoba, zden):
        td = osoba.typ_doch
        return "StarDoch" if td==TypDochodku.STAROBNY else "InvDoch" if td== TypDochodku.INVALIDNY else "StarDoch" if td==TypDochodku.STAROBNY else "DoVP"

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        datum = self.datum_ukoncenia if self.datum_ukoncenia else self.datum_do #Dohoda môže byť ukončená predčasne
        if datum <zden: return []
        kdatum =  date(zden.year, zden.month+1, zden.day) if zden.month+1 <= 12 else  date(zden.year+1, 1, 1)
        if datum >= kdatum: return []
        platba = {
                "nazov":f"DoVP odmena (int. prevod)" if self.interny_prevod==AnoNie.ANO else "DoVP odmena",
                "suma": -Decimal(self.vyplatena_odmena if self.datum_ukoncenia else self.odmena_celkom),
                "datum": zden,
                "subjekt": f"{self.zmluvna_strana.priezvisko}, {self.zmluvna_strana.meno}", 
                "osoba": self.zmluvna_strana,
                "vynimka": self.vynimka,
                "cislo": self.cislo,
                "zdroj": self.zdroj,
                "zakazka": self.zakazka,
                "ekoklas": self.ekoklas
                }
        return [platba]
 
    # test platnosti dát
    def clean(self): 
        num_days = (self.datum_do - self.datum_od).days
        if num_days > 366:
            raise ValidationError({"num_days": f"Doba platnosti dohody presahuje maximálnu povolenú dobu 12 mesiacov."})
        if self.hod_celkom > 350:
            raise ValidationError({"hod_celkom": f"Celkový počet {pocet_hodin} hodín maximálny zákonom povolený povolený počet 350."})
        if self.datum_ukoncenia and not self.vyplatena_odmena:
            raise ValidationError({"vyplatena_odmena":f"Ak je vyplnené pole 'Dátum ukončenia', musí byť vyplnené aj pole 'Vyplatená odmena'."})

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

    def cerpanie_rozpoctu(self, zden):
        return []
    class Meta:
        verbose_name = 'Dohoda o bigádnickej práci študentov'
        verbose_name_plural = 'PaM - Dohody o bigádnickej práci študentov'
    def __str__(self):
        return f"{self.zmluvna_strana}; {self.cislo}"

class DoPC(Dohoda):
    oznacenie = "DoPC"
    dodatok_k = models.ForeignKey('self',
            help_text = "Ak ide len o dodatok k existujúcej DoPC, zadajte ju v tomto poli.<br />V tomto prípade sa pri ukladaní číslo tohohto dodatku zmení na číslo dohody doplnené o text 'Dodatok'. <br />Ďalší postup vytvárania dodatku je rovnaký ako v prípade DoVP",
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
            help_text = "Dohodnutý počet odpracovaných hodín za mesiac, najviac 42",
            max_digits=8, 
            decimal_places=1, 
            null=True)
    datum_ukoncenia = models.DateField('Dátum ukončenia',
            help_text = "Zadajte dátum predčasného ukončenia platnosti dohody",
            blank = True,
            null=True)
    zmena_zdroja = models.TextField("Zmena zdroja alebo odmeny", 
                                    help_text = "Zadajte po riadkoch mesiace (v rozsahu platnosti dohody), v ktorých sa zdroj, zákazka alebo suma odlišujú od svojich preddefinovaných hodnôt, a to v tvare <em>RRRR/MM;zdroj;zákazka;odmena</em>.<br />Vždy treba zadať všetky tri položky, aj keď sa zmenila len jedna z týchto hodnôt.<br />Obvyklé hodnoty pre pár <strong>zdroj;zákazka</strong> sú: <strong>42;42002200</strong>, <strong>111;11010001</strong> a <strong>111;11070002</strong>.", 
            max_length=500,
            blank=True,
            null=True)
    history = HistoricalRecords()

    #Konverzia typu dochodku na pozadovany typ vo funkcii DohodarOdvody
    @staticmethod
    def td_konv(osoba, zden):
        td = osoba.typ_doch
        return "StarDoch" if td==TypDochodku.STAROBNY else "InvDoch" if td== TypDochodku.INVALIDNY else "StarDoch" if td==TypDochodku.STAROBNY else "DoPC"

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        datum_od_1 = date(self.datum_od.year, self.datum_od.month, 1)
        if zden < datum_od_1: return []
        if self.datum_ukoncenia and zden > self.datum_ukoncenia: return []
        if zden > self.datum_do: return []

        zdroj = None
        zakazka = None
        odmena_mesacne = None
        if self.zmena_zdroja:
            zz = re.findall(r"%d/%02d[,; ]+([0-9]+)[,; ]+([0-9,.]+)[,; ]([0-9,.]+)"%(zden.year, zden.month), self.zmena_zdroja)
            #zz: zdroj, zákazka, odmena
            if zz:
                print("DoPC: ",self)
                if zz[0][0]== "42":
                    zdroj = Zdroj.objects.get(kod="42")
                    zakazka = TypZakazky.objects.get(kod="42002200")
                    odmena_mesacne = float(zz[0][2].replace(",","."))
                elif zz[0][0]== "111":
                    kod = {"11010001": "11010001 spol. zák.", "11070002": "11070002 Beliana"}
                    zdroj = Zdroj.objects.get(kod="111")
                    zakazka = TypZakazky.objects.get(kod=kod[zz[0][1]])
                    odmena_mesacne = float(zz[0][2].replace(",","."))

        zdroj = zdroj if zdroj else self.zdroj
        zakazka = zakazka if zakazka else self.zakazka
        odmena_mesacne = odmena_mesacne if odmena_mesacne else self.odmena_mesacne
        platba = {
                "nazov":f"DoPC odmena",
                "suma": -Decimal(odmena_mesacne),
                "datum": zden,
                "subjekt": f"{self.zmluvna_strana.priezvisko}, {self.zmluvna_strana.meno}", 
                "osoba": self.zmluvna_strana,
                "vynimka": self.vynimka,
                "cislo": self.cislo,
                "zdroj": zdroj,
                "zakazka": zakazka,
                "ekoklas": self.ekoklas
                }
        return [platba]

    class Meta:
        verbose_name = 'Dohoda o pracovnej činnosti'
        verbose_name_plural = 'PaM - Dohody o pracovnej činnosti'
    # test platnosti dát
    def clean(self): 
        if self.hod_mesacne > 42:
            raise ValidationError(f"Počet hodín mesačne {self.hod_mesacne} presahuje maximálny zákonom povolený počet 42.")

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
        #socialne_zam, socialne_prac, zdravotne_zam, zdravotne_prac = DohodarOdvody(vyplatena_odmena, td, self.dohoda.datum_od, vynimka_suma) 
        #self.poistne_zamestnavatel = socialne_zam+zdravotne_zam
        #self.poistne_dohodar = socialne_praczdravotne_prac
        #self.dan_dohodar = (vyplatena_odmena - self.poistne_dohodar) * DAN_Z_PRIJMU / 100
        #self.na_ucet = vyplatena_odmena - self.poistne_dohodar - self.dan_dohodar

        #uložiť dátum vyplatenia do dohody. V prípade opakovaného vyplácania DoPC a DoBPS sa pridáva ďalší dátum do zoznamu
        vypl = "%s, "%self.dohoda.vyplatene if self.dohoda.vyplatene else ""
        self.dohoda.vyplatene=f"{vypl}{self.datum_vyplatenia}"
        self.dohoda.save()
        pass

    class Meta:
        verbose_name = 'Vyplatenie dohody'
        verbose_name_plural = 'PaM - Vyplácanie dohôd'


def pokladna_upload_location(instance, filename):
    return os.path.join(POKLADNA_DIR, filename)
class Pokladna(models.Model):
    oznacenie = "Po"
    cislo = models.CharField("Číslo záznamu", 
        max_length=50)
    typ_transakcie = models.CharField("Typ záznamu", 
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
    cislo_VPD = models.IntegerField("Poradové číslo PD",
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
    subor_doklad = models.FileField("Doklad o úhrade",
            help_text = "Súbor so zoskenovaným dokladom o úhrade",
            upload_to=pokladna_upload_location, 
            null = True, blank = True)
    subor_vpd = models.FileField("Súbor PD",
            help_text = "Súbor pokladničného dokladu (VPD, PPD). Generuje sa akciou 'Vytvoriť PD'",
            upload_to=pokladna_upload_location, 
            null = True, blank = True)
    datum_softip = models.DateField('Dátum THS',
            help_text = "Dátum vytvorenia zoznamu PD pre THS. Vypĺňa sa automaticky akciou 'vytvoriť zoznam PD pre THS'",
            blank = True,
            null=True
            )
    popis = models.CharField("Popis platby", 
            help_text = "Stručný popis transakcie. Ak sa dá, v prípade PPD uveďte číslo súvisiaveho VPD",
            max_length=60,
            null=True
            )
    poznamka = models.CharField("Poznámka", 
            max_length=60,
            blank = True,
            null=True
            )
    zdroj = models.ForeignKey(Zdroj,
            help_text = "V prípade dotácie nechajte prázdne, inak je povinné",
            on_delete=models.PROTECT,
            related_name='%(class)s_pokladna',
            blank = True,
            null = True
            )
    zakazka = models.ForeignKey(TypZakazky,
            on_delete=models.PROTECT,
            help_text = "V prípade dotácie nechajte prázdne, inak je povinné",
            verbose_name = "Typ zákazky",
            related_name='%(class)s_pokladna',
            blank = True,
            null = True
            )
    ekoklas = models.ForeignKey(EkonomickaKlasifikacia,
            on_delete=models.PROTECT,
            help_text = "V prípade dotácie nechajte prázdne, inak je povinné",
            verbose_name = "Ekonomická klasifikácia",
            related_name='%(class)s_pokladna',
            blank = True,
            null = True
            )
    cinnost = models.ForeignKey(Cinnost,
            on_delete=models.PROTECT,
            help_text = "V prípade dotácie nechajte prázdne, inak je povinné",
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
            if self.typ_transakcie == TypPokladna.VPD:
                if not self.cislo_VPD:
                    self.cislo_VPD = nasledujuce_VPD()
                    if self.suma >= 0:
                        chyby["suma"] = "V prípade  výdavkového PD musí byť pole 'Suma' záporné"
            else:
                if not self.cislo_VPD:
                    self.cislo_VPD = nasledujuce_PPD()
                    if self.suma <= 0:
                        chyby["suma"] = "V prípade príjmového PD musí byť pole 'Suma' kladné"
            if not self.zamestnanec:
                chyby["zamestnanec"] = "V prípade PD treba pole 'Zamestnanec' vyplniť"
            if not self.zakazka:
                chyby["zakazka"] = "V prípade PD treba pole 'Typ zákazky' vyplniť"
            if not self.zdroj:
                chyby["zdroj"] = "V prípade PD treba pole 'Zdroj' vyplniť"
            if not self.ekoklas:
                chyby["ekoklas"] = "V prípade PD treba pole 'Ekonomická klasifikácia' vyplniť"
            if not self.cinnost:
                chyby["cinnost"] = "V prípade PD treba pole 'Činnosť' vyplniť"
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
