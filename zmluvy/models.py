import datetime
from django.db import models
from django.utils import timezone

class AnoNie(models.TextChoices):
    ANO = 'ano', 'Áno'
    NIE = 'nie', 'Nie'


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
    email = models.CharField("Email", max_length=200)
    titul_pred_menom = models.CharField("Titul pred menom", max_length=100, blank=True) #optional
    meno = models.CharField("Meno", max_length=200)
    priezvisko = models.CharField("Priezvisko", max_length=200)
    titul_za_menom = models.CharField("Titul za menom", max_length=100, blank=True)     #optional
    rodne_cislo = models.CharField("Rodné číslo", max_length=20, blank=True)     #optional
    #pub_date = models.DateTimeField('date published')

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
    zdanit = models.CharField(max_length=3, choices=AnoNie.choices, blank=True) 

    def __str__(self):
        return self.rs_login
    class Meta:
        verbose_name = 'Autor'
        verbose_name_plural = 'Autori'


#1057	TrnkaAlfred	atrnka@truni.sk	prof. RNDr.	Alfréd	Trnka	PhD.	1729
#   oo = Osoba(rs_uid = 1057, rs_login = "TrnkaAlfred", email = "atrnka@truni.sk", titul_pred_menom = "RNDr.", meno = "Alfréd", priezvisko = "Trnka", titul_za_menom = "PhD.", posobisko = "Truni, Trenčín")
#   oo.save()
#   zz=Zmluva(zmluvna_strana=oo, cislo_zmluvy="1729")
#   zz.save()

#1062	AstalosBoris	boris.astalos@SNM.sk		Boris	Astaloš		40/2019
#   oo = Osoba(rs_uid = 1062, rs_login = "AstalosBoris", email = "boris.astalos@SNM.sk", meno = "Boris", priezvisko = "Astaloš", posobisko = "Slovenské národné múzeum, Bratislava")
#   oo.save()
#   zz=Zmluva(zmluvna_strana=oo, cislo_zmluvy="40/2019")
#   zz.save()

class Zmluva(models.Model):
    cislo_zmluvy = models.CharField("Číslo zmluvy", max_length=50)
    datum_pridania = models.DateTimeField('Dátum pridania', auto_now_add=True)
    datum_aktualizacie = models.DateTimeField('Dátum aktualizácie', auto_now=True)

    def __str__(self):
        return self.cislo_zmluvy
    class Meta:
        abstract = True
        verbose_name = 'Zmluva'
        verbose_name_plural = 'Zmluvy'

class ZmluvaAutor(Zmluva):
    zmluvna_strana = models.ForeignKey(OsobaAutor, on_delete=models.CASCADE)
    odmena = models.FloatField("Odmena/AH", default=0)  #Eur/AH (36 000 znakov)
    class Meta:
        verbose_name = 'Autorská zmluva'
        verbose_name_plural = 'Autorské zmluvy'

