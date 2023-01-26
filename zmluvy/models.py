from datetime import date
from django.db import models
from django.utils import timezone
from django.contrib import messages
from ipdb import set_trace as trace
from zmluvy.storage import OverwriteStorage
from django.utils.safestring import mark_safe

from beliana.settings import CONTRACTS_DIR_NAME, RLTS_DIR_NAME, TMPLTS_DIR_NAME, TAX_AGMT_DIR_NAME
import os,re

from uctovnictvo.models import EkonomickaKlasifikacia, Zdroj, TypZakazky

#záznam histórie
#https://django-simple-history.readthedocs.io/en/latest/admin.html
from simple_history.models import HistoricalRecords

class AnoNie(models.TextChoices):
    ANO = 'ano', 'Áno'
    NIE = 'nie', 'Nie'

class StavZmluvy(models.TextChoices):
    #POZIADAVKA = "odoslana_poziadavka", "Odoslaná požiadavka na sekretariát"#Autorovi bol odoslaný dotazník na vyplnenie
    ODOSLANY_DOTAZNIK = "odoslany_dotaznik", "Odoslaný dotazník autorovi"#Autorovi bol odoslaný dotazník na vyplnenie
    VYTVORENA = "vytvorena", "Vytvorená"                        #Úvodný stav, ak sa zmluva vytvára v EnÚ
    ODOSLANA_AUTOROVI = "odoslana_autorovi", "Daná autorovi na podpis"
    VRATENA_OD_AUTORA = "vratena_od_autora", "Vrátená od autora"
    ZVEREJNENA_V_CRZ = "zverejnena_v_crz", "Platná / Zverejnená v CRZ" #Nemusí byť v CRZ, ak bola uzatvorená pred r. 2012
    NEPLATNA = "neplatna", "Neplatná / Nebola verejnená v CRZ"  #Zmluva nie je platná pokiaľ nebola v CRZ zverejnená do 30 dní od podpísania

# Create your models here.     
# Abstraktná trieda so všetkými spoločnými poľami, nepoužívaná samostatne
class PersonCommon(models.Model):
    # IBAN alebo aj kompletný popis s BIC a číslom účtu
    bankovy_kontakt = models.CharField("Bankový kontakt", 
            help_text = "Zadajte IBAN účtu autora (s medzerami po štvoriciach).",
            max_length=200, null=True, blank=True)
    adresa_ulica = models.CharField("Adresa – ulica a číslo domu", max_length=200, null=True, blank=True)
    adresa_mesto = models.CharField("Adresa – PSČ a mesto", max_length=200, null=True, blank=True)
    adresa_stat = models.CharField("Adresa – štát", max_length=100, null=True, blank=True)
    koresp_adresa_institucia = models.CharField("Korešpondenčná adresa – institucia", max_length=200, null=True, blank=True)
    koresp_adresa_ulica = models.CharField("Korešpondenčná adresa – ulica a číslo domu", max_length=200, null=True, blank=True)
    koresp_adresa_mesto = models.CharField("Korešpondenčná adresa – PSČ a mesto", max_length=200, null=True, blank=True)
    koresp_adresa_stat = models.CharField("Korešpondenčná adresa – štát", max_length=100, null=True, blank=True)
    datum_aktualizacie = models.DateField('Dátum aktualizácie', auto_now=True)
    class Meta:
        abstract = True

# spol. s r. o., alebo iné, majú 
#class PartnerOrganizacia(PersonCommon)L

# cesta k súborom s dohodou o nezdaňovaní
def tax_agmt_path(instance, filename):
    return os.path.join(TAX_AGMT_DIR_NAME, filename)

# nie je nevyhnutne v RS (jaz. redaktor a pod)
class FyzickaOsoba(PersonCommon):
    email = models.EmailField("Email", 
            max_length=200, 
            null=True) 
    titul_pred_menom = models.CharField("Titul pred menom", max_length=100, null=True, blank=True) #optional
    meno = models.CharField("Meno", max_length=200)
    priezvisko = models.CharField("Priezvisko", max_length=200)
    titul_za_menom = models.CharField("Titul za menom", max_length=100, null=True, blank=True)     #optional
    rodne_cislo = models.CharField("Rodné číslo", 
            help_text = "Občania SR: rodné číslo, inak dátum narodenia ",
            max_length=20, 
            null=True, 
            blank=True) 
    nevyplacat = models.CharField("Nevyplácať",
            help_text = "Zvoľte 'Áno', ak sa honorár nemá vyplácať (napr. ak autor zomrel a nie je jasné, komu honorár poslať). V poznámke uveďte konkrétny dôvod.",
            max_length=3, choices=AnoNie.choices, null=True, blank=True) 
    rezident = models.CharField("Rezident SR", 
            help_text = "Uveďte, či je autor daňovník s neobmedzenou daňovou povinnosťou v SR (daňový rezident SR). Ak autor nie je daňový rezident SR, tak sa jeho honorár nezdaňuje.",
            max_length=3, 
            choices=AnoNie.choices, 
            default = AnoNie.ANO,
            null=True)
    zdanit = models.CharField("Zdaniť",
            help_text = "Zvoľte 'Nie', ak autor podpísal dohodu o nezdaňovaní. V tom prípade treba vyplniť aj polia 'Dohoda podpísaná' a 'Dohoda o nezdaňovaní'.",
            max_length=3, 
            choices=AnoNie.choices, 
            default = AnoNie.ANO,
            null=True) 
    # opakované uploadovanie súboru vytvorí novú verziu
    #subor = models.FileField("Súbor",upload_to=TMPLTS_DIR_NAME, null = True, blank = True)
    # opakované uploadovanie súboru prepíše existujúci súbor (nevytvorí novú verziu)
    dohodasubor = models.FileField("Dohoda o nezdaňovaní", 
            help_text = "Vložte pdf súbor so zoskenovanou dohodou o nezdaňovaní.",
            storage=OverwriteStorage(), upload_to=tax_agmt_path, null = True, blank = True)
    datum_dohoda_podpis = models.DateField('Dohoda podpísaná',
            help_text = "Zadajte dátum podpisu dohody o nezdaňovaní.",
            blank=True, null=True)
    datum_dohoda_oznamenie = models.DateField('Dohoda oznámená', 
            help_text = "Zadajte dátum oznámenia existencie dohody o nezdaňovaní Finančnej správe. Oznámenie sa posiela v termíne do konca januára roku, ktorý nasleduje po roku, keď po prvýkrát nebol honorár zdanený.",
            blank=True, null=True)
    poznamka = models.CharField("Poznámka", max_length=200, blank=True)
    #pub_date = models.DateField('date published')

    #priezvisko, meno
    def pm(self):
        return f"{self.priezvisko}, {self.meno}"

    #meno priezvisko
    def mp(self):
        return f"{self.meno} {self.priezvisko}"

    #meno priezvisko, tituly
    def mpt(self):
        mpt = self.mp()
        if self.titul_pred_menom:
            mpt = f"{self.titul_pred_menom} {mpt}"
        if self.titul_za_menom:
            mpt = f"{mpt}, {self.titul_za_menom}"
        return mpt

    class Meta:
        abstract = True

#class PartnerOsoba(FyzickaOsoba):

#Autor, Konzultant, Garant, v RS s loginom PriezviskoMeno`
class OsobaAuGaKo(FyzickaOsoba):
    rs_uid = models.IntegerField("Uid v RS", null=True, blank=True) #not needed, kept for eventual future usage
    rs_login = models.CharField("Login v RS", max_length=100)
    posobisko = models.CharField("Pôsobisko", max_length=200, null=True, blank=True)       #optional
    odbor = models.CharField("Odbor", max_length=200, null=True, blank=True)
    #v_RS_od = models.DateField('V RS od', blank=True)

    class Meta:
        abstract = True
        verbose_name = 'Autor/Garant/Konzultant'
        verbose_name_plural = 'Autor/Garant/Konzultant'

class OsobaAutor (OsobaAuGaKo):
    preplatok = models.DecimalField("Preplatok", max_digits=8, decimal_places=2, default=0)
    history = HistoricalRecords()
    def __str__(self):
        return f"{self.rs_login} A"
    class Meta:
        verbose_name = 'Autor'
        verbose_name_plural = 'Autori'

class OsobaGrafik (FyzickaOsoba):
    history = HistoricalRecords()
    def __str__(self):
        return f"{self.priezvisko}{self.meno}G"
    class Meta:
        verbose_name = 'Grafik'
        verbose_name_plural = 'Grafici'

# cesta k súborom autorských a výtvarných zmlúv
def contract_path(instance, filename):
    return os.path.join(CONTRACTS_DIR_NAME, filename)

class Zmluva(models.Model):
    cislo = models.CharField("Číslo zmluvy", max_length=50)
    datum_pridania = models.DateField('Dátum pridania', auto_now_add=True)
    datum_aktualizacie = models.DateTimeField('Dátum aktualizácie', auto_now=True)
    stav_zmluvy = models.CharField(max_length=20,
            #help_text = "Z ponuky zvoľte aktuálny stav zmluvy. Autorský honorár môže byť vyplatený len vtedy, keď je v stave 'Platná / Zverejnená v CRZ.",
            help_text = '<font color="#aa0000">Zvoliť aktuálny stav zmluvy</font> (po každej jeho zmene).',
            choices=StavZmluvy.choices, blank=True) 
    url_zmluvy = models.URLField('URL zmluvy', 
            help_text = "Zadajte URL pdf súboru zmluvy zo stránky CRZ.",
            null = True)
    zmluva_odoslana= models.DateField('Autorovi na podpis ',
            help_text = 'Dátum odovzdania zmluvy na sekretariát na odoslanie na podpis (poštou). Vytvorí sa záznam v <a href="/admin/dennik/dokument/">denníku prijatej a odoslanej pošty</a>.',
            null=True,
            blank=True)
    zmluva_vratena= models.DateField('Vrátená podpísaná ',
            help_text = 'Dátum obdržania podpísanej zmluvy (poštou). Dátum sa zapíše do <a href="/admin/dennik/dokument/">denníka prijatej a odoslanej pošty</a>.',
            null=True, 
            blank=True)
    datum_zverejnenia_CRZ = models.DateField('Platná od / dátum CRZ', 
            help_text = "Zadajte dátum účinnosti zmluvy (dátum zverejnenia v CRZ + 1 deň). <br />Ak autor podpísal dohodu o nezdaňovaní, vyplňte súvisiace polia v údajoch autora.",
            null=True)
    vygenerovana_subor = models.FileField("Vygenerovaný súbor zmluvy", 
            help_text = "Súbor zmluvy na poslanie autorovi na podpis, vygenerovaný akciou 'Vytvoriť súbory zmluvy'.",
            storage=OverwriteStorage(), upload_to=contract_path, null = True, blank = True)
    vygenerovana_crz_subor = models.FileField("Vygenerovaný súbor zmluvy pre CRZ", 
            help_text = "Anonymizovaný súbor zmluvy na vloženie do CRZ, vygenerovaný akciou 'Vytvoriť súbory zmluvy'. Pred vložením do CRZ treba aktualizovať dátum podpisu.",
            storage=OverwriteStorage(), upload_to=contract_path, null = True, blank = True)
    podpisana_subor = models.FileField("Podpísaná zmluva", 
            help_text = "Vložte pdf súbor so zoskenovanou podpísanou zmluvou.",
            storage=OverwriteStorage(), upload_to=contract_path, null = True, blank = True)

    def __str__(self):
        return self.cislo
    class Meta:
        abstract = True
        verbose_name = 'Zmluva'
        verbose_name_plural = 'Zmluvy'

class ZmluvaAutor(Zmluva):
    oznacenie = "A"    #v čísle faktúry, A-2021-123
    # Polia
    # v OsobaAutor je pristup k zmluve cez 'zmluvaautor'
    #models.PROTECT: Prevent deletion of the referenced object
    #related_name: v admin.py umožní zobrazit zmluvy autora v zozname autorov cez pole zmluvy_link 
    zmluvna_strana = models.ForeignKey(OsobaAutor, on_delete=models.PROTECT, related_name='zmluvy')    
    honorar_ah = models.DecimalField("Honorár/AH", max_digits=8, decimal_places=2) #Eur/AH (36 000 znakov)
    history = HistoricalRecords()

    # Koho uviesť ako adresata v denniku
    def adresat(self):
        return self.zmluvna_strana.rs_login

    class Meta:
        verbose_name = 'Autorská zmluva'
        verbose_name_plural = 'Autorské zmluvy'

class ZmluvaGrafik(Zmluva):
    oznacenie = "V"    #v čísle faktúry, A-2021-123
    # Polia
    #models.PROTECT: Prevent deletion of the referenced object
    #related_name: v admin.py umožní zobrazit zmluvy autora v zozname autorov cez pole zmluvy_link 
    zmluvna_strana = models.ForeignKey(OsobaGrafik, on_delete=models.PROTECT, related_name='zmluvagrafik')
    history = HistoricalRecords()
    # Koho uviesť ako adresata v denniku
    def adresat(self):
        return self.zmluvna_strana

    #priezvisko, meno
    def pm(self):
        return self.zmluvna_strana.pm()

    class Meta:
        verbose_name = 'Výtvarná zmluva'
        verbose_name_plural = 'Výtvarné zmluvy'
    def __str__(self):
        return f"{self.zmluvna_strana}-{self.cislo}"

#Abstraktná trieda pre platby za autorské a výtvarné zmluvy
class Platba(models.Model):
    datum_uhradenia = models.DateField('Dátum vyplatenia', null=True, blank=True)
    #zmluva príp. zoznam zmlúv, podľa ktorých sa vyplácalo
    honorar = models.DecimalField("Honorár", max_digits=8, decimal_places=2, null=True, blank=True)
    uhradena_suma = models.DecimalField("Uhradená suma", max_digits=8, decimal_places=2, default=0, blank=True)
    odvod_LF = models.DecimalField("Odvod aut. fondu", max_digits=8, decimal_places=2, null=True, blank=True)
    odvedena_dan = models.DecimalField("Odvedená daň", max_digits=8, decimal_places=2, null=True, blank=True)
    class Meta:
        abstract = True

class PlatbaAutorskaOdmena(Platba):
    #cislo: priečinok, z ktorého bola platba importovaná
    cislo = models.CharField("Obdobie", max_length=20)  
    zmluva = models.CharField("Zmluva", max_length=200)
    #related_name: v admin.py umožní zobrazit platby autora v zozname autorov cez pole platby_link 
    autor = models.ForeignKey(OsobaAutor, on_delete=models.PROTECT, related_name='platby')
    preplatok_pred = models.DecimalField("Preplatok pred", max_digits=8, decimal_places=2)
    honorar_rs = models.DecimalField("Honorár (RS)", max_digits=8, decimal_places=2)
    honorar_webrs = models.DecimalField("Honorár (WEBRS)", max_digits=8, decimal_places=2)
    znaky_rs = models.DecimalField("Počet znakov (RS)", max_digits=8, decimal_places=2)
    znaky_webrs = models.DecimalField("Počet znakov (WEBRS)", max_digits=8, decimal_places=2)
    preplatok_po = models.DecimalField("Preplatok po", max_digits=8, decimal_places=2)
    def __str__(self):
        return f"{self.autor.priezvisko}-{self.cislo}"


    # executed after 'save'
    #def clean(self):
        #if getattr(self, 'autor', None) is None: # check that current instance has 'autor' attribute not set
            #self.autor = self.zmluva.zmluvna_strana

    class Meta:
        verbose_name = 'Aut. honorár po autoroch'
        verbose_name_plural = 'Aut. honoráre po autoroch'

class VytvarnaObjednavkaPlatba(models.Model):
    oznacenie = "VO"    #čislo objednávky výtvarného diela
    #related_name: v admin.py umožní zobrazit platby autora v zozname autorov cez pole platby_link 
    cislo = models.CharField("Číslo objednávky", max_length=50, null=True)
    vytvarna_zmluva = models.ForeignKey(ZmluvaGrafik, on_delete=models.PROTECT, related_name = "vytvarne_platby")
    objednane_polozky = models.TextField("Objednané položky", 
            help_text = mark_safe("Po riadkoch zadajte objednávané položky so štyrmi poľami oddelenými bodkočiarkou v poradí: <b>Popis</b>; <b>Typ</b>; <b>Množstvo</b>; <b>Cena za jednotku</b>.<br />Ako typ uveďte: mapa, fotografia, čb perovka, farebná kresba.<br />Po vyplnení položiek vytvorte súbor objednávky akciou 'Vytvoriť súbor objednávky'.<br /><strong>Honorár sa dáva na vyplatenie jednorázovo až po dodaní všetkých objednaných položiek</strong>."),
            null=True,
            max_length=5000)
    subor_objednavky = models.FileField("Vygenerovaná objednávka", 
            help_text = "Súbor objednávky na poslanie autorovi na podpis, vygenerovaný akciou 'Vytvoriť súbor objednávky'.",
            storage=OverwriteStorage(), upload_to=contract_path, null = True, blank = True)
    datum_objednavky = models.DateField('Dátum objednávky',
            help_text = "Dátum odoslania objednávky autorovi (mailom)",
            null=True)
    datum_dodania = models.DateField('Dátum dodania',
            help_text = "Dátum dodania objednaných položiek",
            null=True)
    honorar = models.DecimalField("Honorár", 
            help_text = "Honorár. Vyplní sa automaticky na základe položiek objednávky spustením akcie 'Vytvoriť súbor objednávky'.<br />Ak autor nedodá všetky objednané položky, pred generovaním príkazu na vyplatenie sumu upravte a do poľa 'Poznámka' uveďte zoznam nedodaných položiek.",
            max_digits=8, 
            decimal_places=2, 
            null=True, 
            blank=True)
    poznamka = models.CharField("Poznámka", max_length=200, blank=True)
    subor_prikaz = models.FileField("Platobný príkaz",
            help_text = f"Súbor generovaný akciou 'Vygenerovať platobný príkaz'.<br /><strong>Po podpísaní dať na sekretariát na odoslanie do účtárne THS</strong>. Následne <strong>vyplňte pole <em>Dané na úhradu dňa</em></strong>.", 
            upload_to=contract_path, 
            null = True, 
            blank = True)
    dane_na_uhradu = models.DateField('Odovzdané na sekretariát dňa',
            help_text = 'Zadajte dátum odovzdania vytlačeného platobného príkazu a krycieho listu na sekretariát na ďalšie spracovanie. <br />Vytvorí sa záznam v <a href="/admin/dennik/dokument/">denníku prijatej a odoslanej pošty</a>, ktorý vyplní sekretariát.',
            blank=True, null=True)
    datum_uhradenia= models.DateField("Uhradené dňa",
            help_text = f'Dátum uhradenia odmeny a dane Finančnej správe (pokiaľ autor nepodpísal zmluvu o nezdaňovaní).',
            null=True, 
            blank=True)
    datum_oznamenia = models.DateField('Oznámené FS', 
            help_text = "Dátum oznámenia výšky zrazenej dane na finančnú správu (termín: do 15. dňa nasledujúceho mesiaca).<br />Nevyplňuje sa, ak sa autor zdaňuje sám.",
            null=True, 
            blank=True)
    #zmluva príp. zoznam zmlúv, podľa ktorých sa vyplácalo
    odvod_LF = models.DecimalField("Odvod aut. fondu", 
            help_text = "Automaticky doplnené akciou 'Vytvoriť platobný príkaz a krycí list pre THS'",
            max_digits=8, decimal_places=2, null=True, blank=True)
    odvedena_dan = models.DecimalField("Odvedená daň", 
            help_text = "Automaticky doplnené akciou 'Vytvoriť platobný príkaz a krycí list pre THS'",
            max_digits=8, decimal_places=2, null=True, blank=True)
    history = HistoricalRecords()

    #priezvisko, meno
    def pm(self):
        return self.vytvarna_zmluva.pm()

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        if not self.datum_uhradenia: return []
        if self.datum_uhradenia <zden: return []
        kdatum =  date(zden.year, zden.month+1, zden.day) if zden.month+1 <= 12 else  date(zden.year+1, zden.month, zden.day)
        if self.datum_uhradenia >= kdatum: return []

        if zden.year==2022 and zden.month < 4:
            zdroj = Zdroj.objects.get(kod="131L")
            zakazka = TypZakazky.objects.get(kod="131L - Beliana")
        else:
            zdroj = Zdroj.objects.get(kod="111")
            zakazka = TypZakazky.objects.get(kod="11070002 Beliana")

        platby = PlatbaAutorskaOdmena.objects.filter(cislo=self.cislo)
        odmeny = [platba.honorar for platba in platby]
        #trace()
        platba = {
                "nazov": "Honoráre výtvarné",
                "suma": -self.honorar,
                "datum": self.datum_uhradenia,
                "subjekt": self.pm(),
                "cislo": self.cislo,
                "zdroj": zdroj,
                "zakazka": zakazka,
                "ekoklas": EkonomickaKlasifikacia.objects.get(kod="633018") #licencie
                }
        return [platba]

    class Meta:
        verbose_name = 'Objednávka a vyplatenie výtvarných diel'
        verbose_name_plural = 'Objednávky a vyplácanie výtvarných diel'
    def __str__(self):
        return f"{self.cislo}-{self.vytvarna_zmluva.zmluvna_strana}"

#https://stackoverflow.com/questions/55543232/how-to-upload-multiple-files-from-the-django-admin
#Vykoná sa len pri vkladaní suborov cez GUI. Pri programovom vytváraní treba cestu nastaviť
def platba_autorska_sumar_upload_location(instance, filename):
    dir_name = instance.platba_autorska_sumar.cislo
    file_name = filename.replace(" ", "-")
    #Vyplacanie_autorskych_honorarov/2021-02/export_vyplatit_rs-gasparik.csv
    return os.path.join(RLTS_DIR_NAME, dir_name, file_name)

class PlatbaAutorskaSumar(models.Model):
    oznacenie = "AH"
    # názvy akcií
    zrusit_platbu_name = "Zrušiť záznam o platbe v databáze"
    vytvorit_podklady_pre_THS_name = "Vytvoriť podklady na vyplatenie autorských honorárov pre THS"
    zaznamenat_platby_do_db_name = "Vytvoriť finálny prehľad o vyplácaní a zaznamenať platby do databázy"

    #cislo: priečinok, z ktorého bola platba importovaná
    datum_importovania = models.DateField('Importované do RS/WEBRS', 
            help_text = "Dátum importovania do RS/WEBRS",
            null=True, 
            blank=True)
    datum_zalozenia = models.DateField('Založené do šanonov', 
            help_text = "Dátum založenia hárku <em>Po autoroch</em> do šanonov.",
            null=True, 
            blank=True)
    datum_oznamenia = models.DateField('Oznámené FS', 
            help_text = "Dátum oznámenia výšky zrazenej dane na finančnú správu (termín: do 15. dňa nasledujúceho mesiaca).",
            null=True, 
            blank=True)
    #platba_zaznamenana: nastavované programovo
    platba_zaznamenana = models.CharField("Platba zaznanenaná v DB", max_length=3, choices=AnoNie.choices, default=AnoNie.NIE)
    cislo = models.CharField("Identifikátor vyplácania",
            help_text = "Identifikátor vyplácania v tvare AH-RRRR-NNN",
            max_length=20, 
            null = True
            )
    vyplatit_ths = models.FileField("Autorské honoráre",
            help_text = f"Súbor generovaný akciou '{vytvorit_podklady_pre_THS_name}'. <br />Súbor obsahuje údaje pre vyplácanie autorských honorárov (hárok <em>Na vyplatenie</em>) a zoznam chýb, ktoré boli pre generovaní zistené (hárok <em>Chyby</em>).<br /> <strong>Hárky <em>Na vyplatenie</em> a <em>Krycí list</em> s údajmi na vyplatenie autorských honorárov treba dať na sekretariát na odoslanie do účtárne THS</strong>. V prípade odoselania e-mailom treba odoslať PDF súbor. Následne <strong>vyplňte pole <em> Honoráre – pre THS</em></strong>", 
            upload_to=platba_autorska_sumar_upload_location, 
            null = True, 
            blank = True)
    datum_uhradenia = models.DateField('Vyplatené THS-kou', 
            help_text = f"Dátum vyplatenia honorárov na základe odoslaných podkladov z poľa <em>{vyplatit_ths.verbose_name}</em> (oznámený účtárňou THS).",
            null=True, blank=True)
    podklady_odoslane= models.DateField('Honoráre – pre THS',
            help_text = f'Dátum odovzdania podkladov z poľa <em>{vyplatit_ths.verbose_name}</em> na vyplatenie autorských honorárov na sekretariát na odoslanie do účtárne THS.',
            null=True, 
            blank=True)
    autori_na_vyplatenie = models.TextField("Vyplácaní autori", 
            help_text = f"Zoznam vyplácaných autorov. Vypĺňa sa automaticky akciou '{vytvorit_podklady_pre_THS_name}'. <br /><strong>Pokiaľ platba autora neprešla, pred vytvorením finálneho prehľadu platieb ho zo zoznamu odstráňte</strong>.", 
            null = True,
            blank = True,
            max_length=2500)
    vyplatene = models.FileField("Finálny prehľad",
            help_text = f"Súbor generovaný akciou '{zaznamenat_platby_do_db_name}'.<br /><strong>Hárky <em>Na vyplatenie</em> a <em>Krycí list</em> s údajmi na vyplatenie zrážkovej dane a odvodov do fondov treba dať na sekretariát na odoslanie do účtárne THS</strong>. V prípade odosielania e-mailom treba odoslať PDF súbor. Následne <strong>vyplňte pole <em>Daň – pre THS</em></strong>.<br /><strong>Hárok <em>Po autoroch</em> treba vytlačiť a po autoroch založiť do šanonov</strong>.", 
            upload_to=platba_autorska_sumar_upload_location, 
            null = True, 
            blank = True)
    kryci_list_odoslany= models.DateField("Daň – pre THS",
            help_text = f'Dátum odovzdania podkladov z poľa <em>{vyplatene.verbose_name}</em> na vyplatenie zrážkovej dane a odvodov do fondov na sekretariát na odoslanie do účtárne THS.',
            null=True, 
            blank=True)
    dan_zaplatena= models.DateField("Daň zaplatená dňa",
            help_text = f'Dátum zaplatenia dane Finančnej správe. Potrebné pri oznamovaní výšky zrazenej dane Finančnej správe.',
            null=True, 
            blank=True)
    import_rs = models.FileField("Importovať do RS",
            help_text = f"Súbor s údajmi o vyplácaní na importovanie do knižného redakčného systému. Po importovaní vyplniť pole <em>{datum_importovania.verbose_name}</em>.",
            upload_to=platba_autorska_sumar_upload_location, 
            null = True, 
            blank = True)
    import_webrs = models.FileField("Importovať do WEBRS",
            help_text = f"Súbor s údajmi o vyplácaní na importovanie do webového redakčného systému. Po importovaní vyplniť pole <em>{datum_importovania.verbose_name}</em>.",
            upload_to=platba_autorska_sumar_upload_location, 
            null = True, 
            blank = True)
    history = HistoricalRecords()

    #čerpanie rozpočtu v mesiaci, ktorý začína na 'zden'
    def cerpanie_rozpoctu(self, zden):
        if not self.datum_uhradenia: return []
        if self.datum_uhradenia <zden: return []
        kdatum =  date(zden.year, zden.month+1, zden.day) if zden.month+1 <= 12 else  date(zden.year+1, zden.month, zden.day)
        if self.datum_uhradenia >= kdatum: return []

        if zden.year==2022 and zden.month < 4:
            zdroj = Zdroj.objects.get(kod="131L")
            zakazka = TypZakazky.objects.get(kod="131L - Beliana")
        else:
            zdroj = Zdroj.objects.get(kod="111")
            zakazka = TypZakazky.objects.get(kod="11070002 Beliana")

        platby = PlatbaAutorskaOdmena.objects.filter(cislo=self.cislo)
        odmeny = [platba.honorar for platba in platby]
        platba = {
                "nazov": "Honoráre autori",
                "suma": -sum(odmeny),
                "datum": self.datum_uhradenia if self.datum_uhradenia else self.datum_importovania,
                "subjekt": "Autori",
                "cislo": self.cislo,
                "zdroj": zdroj,
                "zakazka": zakazka,
                "ekoklas": EkonomickaKlasifikacia.objects.get(kod="633018") #licencie
                }
        return [platba]

    class Meta:
        verbose_name = 'Vyplácanie aut. honorárov'
        verbose_name_plural = 'Vyplácanie aut. honorárov'
        permissions = [
            ('pas_notif_fs', 'Prijímať notifikácie o termínoch FS'),
        ]
    def __str__(self):
        return f"Vyplácanie AH za {self.cislo}"

##https://stackoverflow.com/questions/55543232/how-to-upload-multiple-files-from-the-django-admin
class PlatbaAutorskaSumarSubor(models.Model):
    # on_delete=models.CASCADE: when a ZmluvaAutor is deleted, upload models are also deleted
    platba_autorska_sumar = models.ForeignKey(PlatbaAutorskaSumar, on_delete=models.CASCADE) 
    file = models.FileField("Súbor",upload_to=platba_autorska_sumar_upload_location, null = True, blank = True)
    class Meta:
        verbose_name = 'Súbor s údajmi o autorských honorároch (exportovaný z RS/WEBRS)'
        verbose_name_plural = 'Súbory aut. honorárov'
    def __str__(self):
        odkial = "webového" if "webrs" in self.file.name else "knižného"
        
        return f"Exportovaný súbor z {odkial} redakčného systému z {self.platba_autorska_sumar.cislo}"

def system_file_path(instance, filename):
    return os.path.join(TMPLTS_DIR_NAME, filename)

class SystemovySubor(models.Model):
    subor_nazov =  models.CharField("Názov", max_length=100)
    subor_popis = models.TextField("Popis/účel", max_length=250)
    # opakované uploadovanie súboru vytvorí novú verziu
    #subor = models.FileField("Súbor",upload_to=TMPLTS_DIR_NAME, null = True, blank = True)
    # opakované uploadovanie súboru prepíše existujúci súbor (nevytvorí novú verziu)
    subor = models.FileField(storage=OverwriteStorage(), upload_to=system_file_path, null = True, blank = True)
    class Meta:
        verbose_name = 'Systémový súbor'
        verbose_name_plural = 'Systémové súbory'
    def __str__(self):
        return(self.subor_nazov)
