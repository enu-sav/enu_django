from datetime import datetime
from django.db import models
from django.utils import timezone
from django.contrib import messages
from ipdb import set_trace as trace
from zmluvy.storage import OverwriteStorage

from beliana.settings import CONTRACTS_DIR_NAME, RLTS_DIR_NAME, TMPLTS_DIR_NAME, TAX_AGMT_DIR_NAME
import os,re


#záznam histórie
#https://django-simple-history.readthedocs.io/en/latest/admin.html
from simple_history.models import HistoricalRecords

class AnoNie(models.TextChoices):
    ANO = 'ano', 'Áno'
    NIE = 'nie', 'Nie'

#ak sa doplni stav pred 'PODPISANA_ENU', treba doplniť test vo funkcii vytvorit_subory_zmluvy
class StavZmluvy(models.TextChoices):
    POZIADAVKA = "odoslana_poziadavka", "Odoslaná požiadavka na sekretariát"#Autorovi bol odoslaný dotazník na vyplnenie
    ODOSLANY_DOTAZNIK = "odoslany_dotaznik", "Odoslaný dotazník autorovi"#Autorovi bol odoslaný dotazník na vyplnenie
    VYTVORENA = "vytvorena", "Vytvorená"                        #Úvodný stav, ak sa zmluva vytvára v EnÚ
    PODPISANA_ENU = "podpisana_enu", "Podpísaná EnÚ"
    ODOSLANA_AUTOROVI = "odoslana_autorovi", "Odoslaná autorovi"
    VRATENA_OD_AUTORA = "vratena_od_autora", "Vrátená od autora"
    ZVEREJNENA_V_CRZ = "zverejnena_v_crz", "Platná / Zverejnená v CRZ" #Nemusí byť v CRZ, ak bola uzatvorená pred r. 2012
    NEPLATNA = "neplatna", "Neplatná / Nebola verejnená v CRZ"  #Zmluva nie je platná pokiaľ nebola v CRZ zverejnená do 30 dní od podpísania

# Create your models here.     
# Abstraktná trieda so všetkými spoločnými poľami, nepoužívaná samostatne
class PersonCommon(models.Model):
    # IBAN alebo aj kompletný popis s BIC a číslom účtu
    bankovy_kontakt = models.CharField("Bankový kontakt", 
            help_text = "Zadajte IBAN účtu autora.",
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
    email = models.EmailField("Email", max_length=200, null=True, blank=True)
    titul_pred_menom = models.CharField("Titul pred menom", max_length=100, null=True, blank=True) #optional
    meno = models.CharField("Meno", max_length=200)
    priezvisko = models.CharField("Priezvisko", max_length=200)
    titul_za_menom = models.CharField("Titul za menom", max_length=100, null=True, blank=True)     #optional
    rodne_cislo = models.CharField("Rodné číslo", 
            help_text = "Občania SR: rodné číslo, inak dátum narodenia ",
            max_length=20, 
            null=True, 
            blank=True) 
    zdanit = models.CharField("Zdaniť",
            help_text = "Zvoľte 'Nie', ak autor podpísal dohodu o nezdaňovaní. V tom prípade treba vyplniť aj polia 'Dohoda podpísaná' a 'Dohoda o nezdaňovaní'.",
            max_length=3, choices=AnoNie.choices, null=True, blank=True) 
    nevyplacat = models.CharField("Nevyplácať",
            help_text = "Zvoľte 'Áno', ak sa honorár nemá vyplácať (napr. ak autor zomrel a nie je jasné, komu honorár poslať). V poznámke uveďte konkrétny dôvod.",
            max_length=3, choices=AnoNie.choices, null=True, blank=True) 
    datum_dohoda_podpis = models.DateField('Dohoda podpísaná',
            help_text = "Zadajte dátum podpisu dohody o nezdaňovaní.",
            blank=True, null=True)
    datum_dohoda_oznamenie = models.DateField('Dohoda oznámená', 
            help_text = "Zadajte dátum oznámenia existencie dohody o nezdaňovaní Finančnej správe. Oznámenie sa posiela v termíne do konca januára roku, ktorý nasleduje po roku, keď po prvýkrát nebol honorár zdanený.",
            blank=True, null=True)
    rezident = models.CharField("Rezident SR", 
            help_text = "Uveďte, či je autor daňovík s neobmedzenou daňovou povinnosťou v SR (daňový rezident SR). Ak autor nie je daňový rezident SR, tak sa jeho honorár nezdaňuje.",
            max_length=3, choices=AnoNie.choices, null=True, blank=True) 
    poznamka = models.CharField("Poznámka", max_length=200, blank=True)
    #pub_date = models.DateField('date published')
    # opakované uploadovanie súboru vytvorí novú verziu
    #subor = models.FileField("Súbor",upload_to=TMPLTS_DIR_NAME, null = True, blank = True)
    # opakované uploadovanie súboru prepíše existujúci súbor (nevytvorí novú verziu)
    dohodasubor = models.FileField("Dohoda o nezdaňovaní", 
            help_text = "Vložte pdf súbor so zoskenovanou dohodou o nezdaňovaní.",
            storage=OverwriteStorage(), upload_to=tax_agmt_path, null = True, blank = True)

    class Meta:
        abstract = True
    def __str__(self):
        return self.rs_login

#class PartnerOsoba(FyzickaOsoba):

#Autor, Konzultant, Garant, v RS s loginom PriezviskoMeno`
class OsobaAuGaKo(FyzickaOsoba):
    rs_uid = models.IntegerField("Uid v RS", null=True, blank=True) #not needed, kept for eventual future usage
    rs_login = models.CharField("Login v RS", max_length=100)
    posobisko = models.CharField("Pôsobisko", max_length=200, null=True, blank=True)       #optional
    odbor = models.CharField("Odbor", max_length=200, null=True, blank=True)
    #v_RS_od = models.DateField('V RS od', blank=True)

    def __str__(self):
        return self.rs_login
    class Meta:
        abstract = True
        verbose_name = 'Autor/Garant/Konzultant'
        verbose_name_plural = 'Autor/Garant/Konzultant'

class OsobaAutor (OsobaAuGaKo):

    # preplatok sposobeny vyplácaním 540 namiesto 360 (a možno aj iný dôvod)
    # výpočet je v súbore Kontrola-Kapcova-2018-2021-milos.ods, hárok Preplatok výpočet a Preplatok num.
    preplatok = models.DecimalField("Preplatok", max_digits=8, decimal_places=2, default=0)
    history = HistoricalRecords()
    def __str__(self):
        return self.rs_login
    class Meta:
        verbose_name = 'Autor'
        verbose_name_plural = 'Autori'

class Zmluva(models.Model):
    cislo_zmluvy = models.CharField("Číslo zmluvy", max_length=50)
    datum_pridania = models.DateField('Dátum pridania', auto_now_add=True)
    datum_aktualizacie = models.DateTimeField('Dátum aktualizácie', auto_now=True)
    stav_zmluvy = models.CharField(max_length=20,
            #help_text = "Z ponuky zvoľte aktuálny stav zmluvy. Autorský honorár môže byť vyplatený len vtedy, keď je v stave 'Platná / Zverejnená v CRZ.",
            help_text = '<font color="#aa0000">Zvoliť aktuálny stav zmluvy</font> (po každej jeho zmene).',
            choices=StavZmluvy.choices, blank=True) 
    url_zmluvy = models.URLField('URL zmluvy', 
            help_text = "Zadajte URL pdf súboru zmluvy zo stránky CRZ.",
            blank = True)
    zmluva_odoslana= models.DateField('Odoslaná na podpis ',
            help_text = "Dátum odoslania zmluvy na podpis (poštou)",
            null=True, 
            blank=True)
    zmluva_vratena= models.DateField('Vrátená podpísaná ',
            help_text = "Dátum obdržania podpísanej zmluvy (poštou)",
            null=True, 
            blank=True)
    datum_zverejnenia_CRZ = models.DateField('Platná od / dátum CRZ', 
            help_text = "Zadajte dátum účinnosti zmluvy (dátum zverejnenia v CRZ + 1 deň).",
            blank=True, null=True)

    def __str__(self):
        return self.cislo_zmluvy
    class Meta:
        abstract = True
        verbose_name = 'Zmluva'
        verbose_name_plural = 'Zmluvy'

# cesta k súborom dohody
def contract_path(instance, filename):
    return os.path.join(CONTRACTS_DIR_NAME, filename)

class ZmluvaAutor(Zmluva):
    oznacenie = "A"    #v čísle faktúry, A-2021-123
    @classmethod
    # určiť číslo novej objednávky
    def nasledujuce_cislo(_):   # parameter treba, aby sa metóda mohla volať ako ZmluvaAutor.nasledujuce_cislo()
        # zoznam objednávok s číslom "FaO2021-123" zoradený vzostupne
        ozn_rok = f"{ZmluvaAutor.oznacenie}-{datetime.now().year}-"
        itemlist = ZmluvaAutor.objects.filter(cislo_zmluvy__istartswith=ozn_rok).order_by("cislo_zmluvy")
        if itemlist:
            latest = itemlist.last().cislo_zmluvy
            nove_cislo = int(re.findall(f"{ozn_rok}([0-9]+)",latest)[0]) + 1
            return "%s%03d"%(ozn_rok, nove_cislo)
        else:
            #sme v novom roku
            return f"{ozn_rok}001"
    # Polia
    # v OsobaAutor je pristup k zmluve cez 'zmluvaautor'
    #models.PROTECT: Prevent deletion of the referenced object
    #related_name: v admin.py umožní zobrazit zmluvy autora v zozname autorov cez pole zmluvy_link 
    zmluvna_strana = models.ForeignKey(OsobaAutor, on_delete=models.PROTECT, related_name='zmluvy')    
    honorar_ah = models.DecimalField("Honorár/AH", max_digits=8, decimal_places=2, default=0) #Eur/AH (36 000 znakov)
    vygenerovana_subor = models.FileField("Vygenerovaný súbor zmluvy", 
            help_text = "Súbor zmluvy na poslanie autorovi na podpis, vygenerovaný akciou 'Vytvoriť súbory zmluvy'.",
            storage=OverwriteStorage(), upload_to=contract_path, null = True, blank = True)
    vygenerovana_crz_subor = models.FileField("Vygenerovaný súbor zmluvy pre CRZ", 
            help_text = "Anonymizovaný súbor zmluvy na vloženie do CRZ, vygenerovaný akciou 'Vytvoriť súbory zmluvy'.",
            storage=OverwriteStorage(), upload_to=contract_path, null = True, blank = True)
    podpisana_subor = models.FileField("Podpísaná zmluva", 
            help_text = "Vložte pdf súbor so zoskenovanou podpísanou zmluvou.",
            storage=OverwriteStorage(), upload_to=contract_path, null = True, blank = True)
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Autorská zmluva'
        verbose_name_plural = 'Autorské zmluvy'

#Abstraktná tieda pre všetky platby
#Súčasť Zmluvy 
class Platba(models.Model):
    datum_uhradenia = models.DateField('Dátum vyplatenia')
    uhradena_suma = models.DecimalField("Uhradená suma", max_digits=8, decimal_places=2, default=0)
    class Meta:
        abstract = True

#Hierarchia:
#Autor
#---Zmluva1
#------Platba1
#------Platba2
class PlatbaAutorskaOdmena(Platba):
    #obdobie: priečinok, z ktorého bola platba importovaná
    obdobie = models.CharField("Obdobie", max_length=20)  
    #zoznam zmlúv, podľa ktorých sa vyplácalo
    zmluva = models.CharField("Zmluva", max_length=200)
    #related_name: v admin.py umožní zobrazit platby autora v zozname autorov cez pole platby_link 
    autor = models.ForeignKey(OsobaAutor, on_delete=models.PROTECT, related_name='platby')
    preplatok_pred = models.DecimalField("Preplatok pred", max_digits=8, decimal_places=2)
    honorar = models.DecimalField("Honorár", max_digits=8, decimal_places=2)
    honorar_rs = models.DecimalField("Honorár (RS)", max_digits=8, decimal_places=2)
    honorar_webrs = models.DecimalField("Honorár (WEBRS)", max_digits=8, decimal_places=2)
    znaky_rs = models.DecimalField("Počet znakov (RS)", max_digits=8, decimal_places=2)
    znaky_webrs = models.DecimalField("Počet znakov (WEBRS)", max_digits=8, decimal_places=2)
    odvod_LF = models.DecimalField("Odvod LF", max_digits=8, decimal_places=2)
    odvedena_dan = models.DecimalField("Odvedená daň", max_digits=8, decimal_places=2)
    preplatok_po = models.DecimalField("Preplatok po", max_digits=8, decimal_places=2)

    # executed after 'save'
    #def clean(self):
        #if getattr(self, 'autor', None) is None: # check that current instance has 'autor' attribute not set
            #self.autor = self.zmluva.zmluvna_strana

    class Meta:
        verbose_name = 'Aut. honorár po autoroch'
        verbose_name_plural = 'Aut. honoráre po autoroch'

#https://stackoverflow.com/questions/55543232/how-to-upload-multiple-files-from-the-django-admin
#Vykoná sa len pri vkladaní suborov cez GUI. Pri programovom vytváraní treba cestu nastaviť
def platba_autorska_sumar_upload_location(instance, filename):
    dir_name = instance.platba_autorska_sumar.obdobie
    file_name = filename.replace(" ", "-")
    #Vyplacanie_autorskych_honorarov/2021-02/export_vyplatit_rs-gasparik.csv
    return os.path.join(RLTS_DIR_NAME, dir_name, file_name)

class PlatbaAutorskaSumar(models.Model):
    #obdobie: priečinok, z ktorého bola platba importovaná
    datum_uhradenia = models.DateField('Vyplatené THS-kou', 
            help_text = "Dátum vyplatenia honorárov na základe odoslaných podkladov (oznámený účtárňou THS). <br /><strong>Nasledujúci krok: spustiť akciu 'Vytvoriť finálny prehľad...'</strong>",
            null=True, blank=True)
    datum_importovania = models.DateField('Importované do RS/WEBRS', 
            help_text = "Dátum importovania do RS/WEBRS",
            null=True, 
            blank=True)
    datum_zalozenia = models.DateField('Založené do šanonov', 
            help_text = "Dátum založenia hárku <em>Po autoroch</em> do šanonov.",
            null=True, 
            blank=True)
    datum_oznamenia = models.DateField('Oznámené FS)', 
            help_text = "Dátum oznámenia nezdanených autorov na finančnú správu (termín: do 15. dňa nasledujýceho mesiaca).",
            null=True, 
            blank=True)
    #platba_zaznamenana: nastavované programovo
    platba_zaznamenana = models.CharField("Platba zaznanenaná v DB", max_length=3, choices=AnoNie.choices, default=AnoNie.NIE)
    obdobie = models.CharField("Identifikátor vyplácania",
            help_text = "Ako identifikátor vyplácania sa použije dátum jeho vytvorenia",
            max_length=20, 
            null = True
            )
    vyplatit_ths = models.FileField("Podklady na vyplatenie",
            help_text = "Súbor generovaný akciou 'Vytvoriť podklady na vyplatenie autorských odmien pre THS'. <br />Súbor obsahuje údaje pre vyplácanie autorských honorárov (hárok <em>Na vyplatenie</em>) a zoznam chýb, ktoré boli pre generovaní zistené (hárok <em>Chyby</em>).<br /> <strong>Definitívnu verziu súboru (len hárku  <em>Na vyplatenie</em>) treba poslať mailom do účtárne THS na vyplatenie.</strong>", 
            upload_to=platba_autorska_sumar_upload_location, 
            null = True, 
            blank = True)
    podklady_odoslane= models.DateField('Podklady odoslané',
            help_text = "Dátum odoslania podkladov na vyplatenie do účtárne THS",
            null=True, 
            blank=True)
    autori_na_vyplatenie = models.TextField("Vyplácaní autori", 
            help_text = "Zoznam vyplácaných autorov. Vypĺňa sa automaticky akciou 'Vytvoriť podklady na vyplatenie autorských odmien pre THS'. <br /><strong>Pokiaľ platba autora neprešla, pred vytvorením finálneho prehľadu platieb ho zo zoznamu odstráňte</strong>.", 
            null = True,
            blank = True,
            max_length=2500)
    vyplatene = models.FileField("Finálny prehľad",
            help_text = "Súbor generovaný akciou 'Vytvoriť finálny prehľad o vyplácaní a zaznamenať platby do databázy'.<br /><strong>Hárok <em>Na vyplatenie</em> treba poslať mailom do účtárne THS na vyplatenie</strong><br /><strong>Hárky <em>Na vyplatenie</em> a <em>Krycí list</em> treba vytlačiť a poslať internou poštou THS-ke</strong><br /><strong>Hárok <em>Po autoroch</em> treba vytlačiť a po autoroch založiť so šanonov</strong>.", 
            upload_to=platba_autorska_sumar_upload_location, 
            null = True, 
            blank = True)
    na_vyplatenie_odoslane= models.DateField("'Na vyplatenie' odoslané",
            help_text = "Dátum odoslania hárku <em>Na vyplatenie</em> do účtárne THS (mailom)</em>",
            null=True, 
            blank=True)
    kryci_list_odoslany= models.DateField("'Krycí list' odoslaný",
            help_text = "Dátum odoslania hárku <em>Krycí list</em> do účtárne THS (internou poštou)</em>",
            null=True, 
            blank=True)
    import_rs = models.FileField("Importovať do RS",
            help_text = "Súbor s údajmi o vyplácaní na importovanie do knižného redakčného systému. Po importovaní vyplniť pole <em>Importované do RS/WEBRS</em>.",
            upload_to=platba_autorska_sumar_upload_location, 
            null = True, 
            blank = True)
    import_webrs = models.FileField("Importovať do WEBRS",
            help_text = "Súbor s údajmi o vyplácaní na importovanie do webového redakčného systému. Po importovaní vyplniť pole <em>Importované do RS/WEBRS</em>.",
            upload_to=platba_autorska_sumar_upload_location, 
            null = True, 
            blank = True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Vyplácanie aut. honorárov'
        verbose_name_plural = 'Vyplácanie aut. honorárov'
        permissions = [
            ('pas_notif_fs', 'Prijímať notifikácie o termínoch FS'),
        ]
    def __str__(self):
        return f"Vyplácanie za obdobie {self.obdobie}"

##https://stackoverflow.com/questions/55543232/how-to-upload-multiple-files-from-the-django-admin
class PlatbaAutorskaSumarSubor(models.Model):
    # on_delete=models.CASCADE: when a ZmluvaAutor is deleted, upload models are also deleted
    platba_autorska_sumar = models.ForeignKey(PlatbaAutorskaSumar, on_delete=models.CASCADE) 
    file = models.FileField("Súbor",upload_to=platba_autorska_sumar_upload_location, null = True, blank = True)
    class Meta:
        verbose_name = 'Súbor aut. honorárov'
        verbose_name_plural = 'Súbory aut. honorárov'
    def __str__(self):
        odkial = "webového" if "webrs" in self.file.name else "knižného"
        
        return f"Exportovaný súbor z {odkial} redakčného systému za obdobie {self.platba_autorska_sumar.obdobie}"

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
