import datetime
from django.db import models
from django.utils import timezone
from django.contrib import messages
from ipdb import set_trace as trace
from zmluvy.storage import OverwriteStorage

from beliana.settings import CONTRACTS_DIR_NAME, RLTS_DIR_NAME, TMPLTS_DIR_NAME
import os


#záznam histórie
#https://django-simple-history.readthedocs.io/en/latest/admin.html
from simple_history.models import HistoricalRecords

from .common import VytvoritAutorskuZmluvu

class AnoNie(models.TextChoices):
    ANO = 'ano', 'Áno'
    NIE = 'nie', 'Nie'

class StavZmluvy(models.TextChoices):
    VYTVORENA = "vytvorena", "Vytvorená"                        #Úvodný stav, ak sa zmluva vytvára v EnÚ
    PRIJATA = "prijata", "Prijatá"                              #Úvodný stav, ak bola zmluva vytvorená mimo EnÚ
    PODPISANA_ENU = "podpisana_enu", "Podpísaná EnÚ"
    ODOSLANA_ZS = "odoslana_zs", "Odoslaná ZS"
    VRATENA_OD_ZS = "vratena_od_zs", "Vrátená od ZS"
    ZVEREJNENA_V_CRZ = "zverejnena_v_crz", "Platná / Zverejnená v CRZ"  #Nemusí byť v CRZ, ak bola uzatvorené pre r. 2012

# Create your models here.     
# Abstraktná trieda so všetkými spoločnými poľami, nepoužívaná samostatne
class PersonCommon(models.Model):
    # IBAN alebo aj kompletný popis s BIC a číslom účtu
    bankovy_kontakt = models.CharField("Bankový kontakt", max_length=200)
    adresa_ulica = models.CharField("Adresa – ulica a číslo domu", max_length=200, null=True, blank=True)
    adresa_mesto = models.CharField("Adresa – PSČ a mesto", max_length=200)
    adresa_stat = models.CharField("Adresa – štát", max_length=100)
    koresp_adresa_institucia = models.CharField("Korešpondenčná adresa – institucia", max_length=200, null=True, blank=True)
    koresp_adresa_ulica = models.CharField("Korešpondenčná adresa – ulica a číslo domu", max_length=200, null=True, blank=True)
    koresp_adresa_mesto = models.CharField("Korešpondenčná adresa – PSČ a mesto", max_length=200, null=True, blank=True)
    koresp_adresa_stat = models.CharField("Korešpondenčná adresa – štát", max_length=10, null=True, blank=True)
    datum_aktualizacie = models.DateField('Dátum aktualizácie', auto_now=True)
    class Meta:
        abstract = True

# spol. s r. o., alebo iné, majú 
#class PartnerOrganizacia(PersonCommon)L

# nie je nevyhnutne v RS (jaz. redaktor a pod)
class FyzickaOsoba(PersonCommon):
    email = models.EmailField("Email", max_length=200)
    titul_pred_menom = models.CharField("Titul pred menom", max_length=100, null=True, blank=True) #optional
    meno = models.CharField("Meno", max_length=200)
    priezvisko = models.CharField("Priezvisko", max_length=200)
    titul_za_menom = models.CharField("Titul za menom", max_length=100, null=True, blank=True)     #optional
    rodne_cislo = models.CharField("Rodné číslo", max_length=20) 
    zdanit = models.CharField("Zdaniť", max_length=3, choices=AnoNie.choices, null=True, blank=True) 
    rezident = models.CharField("Rezident SR", max_length=3, choices=AnoNie.choices, null=True, blank=True) 
    poznamka = models.CharField("Poznámka", max_length=200, blank=True)
    #pub_date = models.DateField('date published')

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
    odbor = models.CharField("Odbor", max_length=200)
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
    stav_zmluvy = models.CharField(max_length=20, choices=StavZmluvy.choices, blank=True) 
    url_zmluvy = models.URLField('URL zmluvy', blank = True)
    datum_zverejnenia_CRZ = models.DateField('Platná od / dátum CRZ', blank=True, null=True)

    def __str__(self):
        return self.cislo_zmluvy
    class Meta:
        abstract = True
        verbose_name = 'Zmluva'
        verbose_name_plural = 'Zmluvy'

class ZmluvaAutor(Zmluva):
    # v OsobaAutor je pristup k zmluve cez 'zmluvaautor'
    #models.PROTECT: Prevent deletion of the referenced object
    #related_name: v admin.py umožní zobrazit zmluvy autora v zozname autorov cez pole zmluvy_link 
    zmluvna_strana = models.ForeignKey(OsobaAutor, on_delete=models.PROTECT, related_name='zmluvy')    
    honorar_ah = models.DecimalField("Honorár/AH", max_digits=8, decimal_places=2, default=0) #Eur/AH (36 000 znakov)
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Autorská zmluva'
        verbose_name_plural = 'Autorské zmluvy'

#https://stackoverflow.com/questions/55543232/how-to-upload-multiple-files-from-the-django-admin
#Vykoná sa len pri vkladaní suborov cez GUI. Pri programovom vytváraní treba cestu nastaviť
def zmluva_autor_upload_location(instance, filename):
    dir_name = "{}-{}".format(instance.zmluva.zmluvna_strana.rs_login, instance.zmluva.cislo_zmluvy.replace("/","-"))
    file_name = filename.replace(" ", "-")
    return os.path.join(CONTRACTS_DIR_NAME, dir_name, file_name)

class ZmluvaAutorSubor(models.Model):
    # on_delete=models.CASCADE: when a ZmluvaAutor is deleted, upload models are also deleted
    zmluva = models.ForeignKey(ZmluvaAutor, on_delete=models.CASCADE) 
    file = models.FileField("Súbor",upload_to=zmluva_autor_upload_location, null = True, blank = True)
    class Meta:
        verbose_name = 'Súbor autorskej zmluvy'
        verbose_name_plural = 'Súbory autorskej zmluvy'



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
    datum_uhradenia = models.DateField('Vyplatené THS-kou', null=True, blank=True)
    datum_importovania = models.DateField('Importované do RS/WEBRS', null=True, blank=True)
    datum_zalozenia = models.DateField('Založené do šanonov (po autoroch)', null=True, blank=True)
    platba_zaznamenana = models.CharField("Platba zaznanenaná v DB", max_length=3, choices=AnoNie.choices, default=AnoNie.NIE)
    obdobie = models.CharField("Obdobie vyplácania", max_length=20)  
    vyplatit_ths = models.FileField("Súbor pre THS-ku",upload_to=platba_autorska_sumar_upload_location, null = True, blank = True)
    vyplatene = models.FileField("Vyplatené",upload_to=platba_autorska_sumar_upload_location, null = True, blank = True)
    import_rs = models.FileField("Importovať do RS",upload_to=platba_autorska_sumar_upload_location, null = True, blank = True)
    import_webrs = models.FileField("Importovať do WEBRS",upload_to=platba_autorska_sumar_upload_location, null = True, blank = True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Vyplácanie aut. honorárov'
        verbose_name_plural = 'Vyplácanie aut. honorárov'
    def __str__(self):
        return f"Vyplácanie za obdobie {self.obdobie}"

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
    subor_nazov =  models.CharField("Názov", max_length=40)
    subor_popis = models.CharField("Popis/účel", max_length=40)
    # opakované uploadovanie súboru vytvorí novú verziu
    #subor = models.FileField("Súbor",upload_to=TMPLTS_DIR_NAME, null = True, blank = True)
    # opakované uploadovanie súboru prepíše existujúci súbor (nevytvorí novú verziu)
    subor = models.FileField(storage=OverwriteStorage(), upload_to=system_file_path, null = True, blank = True)
    class Meta:
        verbose_name = 'Systémový súbor'
        verbose_name_plural = 'Systémové súbory'
    def __str__(self):
        return(self.subor_nazov)
