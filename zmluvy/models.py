import datetime
from django.db import models
from django.utils import timezone
from django.contrib import messages
from ipdb import set_trace as trace


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
    ZVEREJNENA_V_CRZ = "zverejnena_v_crz", "Zverejnená v CRZ"

# Create your models here.     
# Abstraktná trieda so všetkými spoločnými poľami, nepoužívaná samostatne
class PersonCommon(models.Model):
    # IBAN alebo aj kompletný popis s BIC a číslom účtu
    bankovy_kontakt = models.CharField("Bankový kontakt", max_length=200, blank=True)
    adresa_ulica = models.CharField("Adresa – ulica a číslo domu", max_length=200, blank=True)
    adresa_mesto = models.CharField("Adresa – PSČ a mesto", max_length=200, blank=True)
    adresa_stat = models.CharField("Adresa – štát", max_length=100, blank=True)
    datum_aktualizacie = models.DateField('Dátum aktualizácie', auto_now=True)
    class Meta:
        abstract = True

# spol. s r. o., alebo iné, majú 
#class PartnerOrganizacia(PersonCommon)L

# nie je nevyhnutne v RS (jaz. redaktor a pod)
class FyzickaOsoba(PersonCommon):
    email = models.EmailField("Email", max_length=200)
    titul_pred_menom = models.CharField("Titul pred menom", max_length=100, blank=True) #optional
    meno = models.CharField("Meno", max_length=200)
    priezvisko = models.CharField("Priezvisko", max_length=200)
    titul_za_menom = models.CharField("Titul za menom", max_length=100, blank=True)     #optional
    rodne_cislo = models.CharField("Rodné číslo", max_length=20, blank=True)     #optional
    zdanit = models.CharField(max_length=3, choices=AnoNie.choices, blank=True) 
    poznamka = models.CharField("Poznámka", max_length=200, blank=True)
    #pub_date = models.DateField('date published')

    class Meta:
        abstract = True
    def __str__(self):
        return self.rs_login

#class PartnerOsoba(FyzickaOsoba):

#Autor, Konzultant, Garant, v RS s loginom PriezviskoMeno`
class OsobaAuGaKo(FyzickaOsoba):
    rs_uid = models.IntegerField("Uid v RS")
    rs_login = models.CharField("Login v RS", max_length=100)
    posobisko = models.CharField("Pôsobisko", max_length=200, blank=True)       #optional
    odbor = models.CharField("Odbor", max_length=200, blank=True)               #optional
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

    # v databaze vytvorit alebo aktualizovat zaznam o zmluve
    def VytvoritZmluvu(self, cislozmluvy, odmena):
        status, msg = VytvoritAutorskuZmluvu(self, cislozmluvy, odmena)
        trace()
        if status == messages.SUCCESS:
            #vytvorit zaznam o zmluve
            o_query_set = ZmluvaAutor.objects.filter(zmluvna_strana=self)
            if o_query_set:
                zm = o_query_set.first()
            else:
                zm = ZmluvaAutor.objects.create(zmluvna_strana=self)
            zm.odmena = odmena
            zm.cislo_zmluvy = cislozmluvy
            datum_pridania = timezone.now(),
            zm.datum_aktualizacie = timezone.now()
            zm.stav_zmluvy = StavZmluvy.VYTVORENA
            zm.save()
        return status, msg

class Zmluva(models.Model):
    cislo_zmluvy = models.CharField("Číslo zmluvy", max_length=50)
    datum_pridania = models.DateField('Dátum pridania', auto_now_add=True)
    datum_aktualizacie = models.DateTimeField('Dátum aktualizácie', auto_now=True)
    stav_zmluvy = models.CharField(max_length=20, choices=StavZmluvy.choices, blank=True) 
    url_zmluvy = models.URLField('URL zmluvy', blank = True)
    datum_zverejnenia_CRZ = models.DateField('Dátum CRZ', blank=True, null=True)

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
    odmena_ah = models.DecimalField("Odmena/AH", max_digits=8, decimal_places=2, default=0) #Eur/AH (36 000 znakov)
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
    odmena = models.DecimalField("Odmena", max_digits=8, decimal_places=2)
    odmena_rs = models.DecimalField("Odmena (RS)", max_digits=8, decimal_places=2)
    odmena_webrs = models.DecimalField("Odmena (WEBRS)", max_digits=8, decimal_places=2)
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
        verbose_name = 'Vyplatená autorská odmena'
        verbose_name_plural = 'Vyplatené autorské odmeny'

class PlatbaAutorskaSumar(models.Model):
    #obdobie: priečinok, z ktorého bola platba importovaná
    datum_uhradenia = models.DateField('Dátum vyplatenia')
    obdobie = models.CharField("Obdobie", max_length=20)  

    class Meta:
        verbose_name = 'Platby sumárne'
        verbose_name_plural = 'Platby sumárne'
