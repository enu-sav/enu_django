from django.db import models
from simple_history.models import HistoricalRecords

class InOut(models.TextChoices):
    PRIJATY = 'prijaty', 'Prijatý'
    ODOSLANY = 'odoslany', 'Odoslaný'

class TypDokumentu(models.TextChoices):
    AZMLUVA = 'autorskazmluva', 'Autorská zmluva'
    FAKTURA = 'faktura', 'Faktúra'
    Zmluva = 'zmluva', 'Zmluva'
    DoVP = 'dovp', 'DoVP'
    DoPC = 'dopc', 'DoPC'
    DoBPS = 'dobps', 'DoBPS'
    INY = 'iny', 'Iný'

class SposobDorucenia(models.TextChoices):
    POSTA = 'posta', 'Pošta'
    IPOSTA = 'iposta', 'Interná pošta'
    MAIL = 'mail', 'E-mail'
    OSOBNE = 'osobne', 'Osobne'

# Create your models here.
class Dokument(models.Model):
    oznacenie = "D"    #v čísle dokument, D-2021-123
    cislo = models.CharField("Číslo", max_length=50)
    inout = models.CharField("Prijatý / odoslaný",
            max_length=20, choices=InOut.choices, null=True)
    typdokumentu = models.CharField("Typ dokumentu",
            max_length=20, choices=TypDokumentu.choices, null=True)
    datum = models.DateField('Dátum prijatia / odoslania',
            help_text = "Dátum prijatia / odoslania dokumentu",
            )
    cislopolozky = models.CharField("Súvisiaca položka", 
            null = True,
            help_text = "Ak je to relevantné, uveďte číslo súvisiacej položky (zmluvy, dohody, faktúry). Pokiaľ položka ešte nie je v Djagu vytvorená (napr. ešte v prípade faktúry), najskôr ju vytvorte a záznam spravte potom)", 
            max_length=200)
    odosielatel = models.CharField("xTyp dokumentu", max_length=200)
    adresat = models.CharField("Odosielateľ / Adresát", 
            help_text = "Uveďte adresáta",
            max_length=200)
    url = models.URLField('URL', 
            help_text = "Zadajte URL.",
            blank = True)
    sposob = models.CharField("Spôsob doručenia",
            help_text = "Zvoľte spôsob, akým bol dokument prijatý/doručený",
            max_length=20, choices=SposobDorucenia.choices, null=True, blank=True) 
    vec = models.CharField("Popis", 
            help_text = "Stručne popíšte obsah, napr. 'Zmluva A-2022-007'",
            max_length=200)
    prijalodoslal = models.CharField("Prijal/odoslal", 
            help_text = "Uveďte meno osoby, ktorá zásielku prijala / odoslala.",
            max_length=50,
            blank = True)
    
    poznamka = models.CharField("Poznámka", max_length=200, blank=True)

    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Dokument'
        verbose_name_plural = 'Prijaté a odoslané dokumenty'
    def __str__(self):
        return(self.cislo)
