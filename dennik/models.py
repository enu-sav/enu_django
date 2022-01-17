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
    cislopolozky = models.CharField("Súvisiaca položka", 
            null = True,
            help_text = "Ak je to relevantné, uveďte číslo súvisiacej položky (zmluvy, dohody, faktúry), inak vložte pomlčku '-'. Pokiaľ položka ešte nie je v Djangu vytvorená (napr. v prípade faktúry), najskôr ju vytvorte a záznam spravte potom).", 
            max_length=200)
    typdokumentu = models.CharField("Typ dokumentu",
            max_length=20, choices=TypDokumentu.choices, 
            help_text = "Uveďte typ dokumentu. <strong>Netreba vypĺňať, ak je vyplnené pole Súvisiaca položka</strong>.",
            blank = True,
            null=True)
    adresat = models.CharField("Odosielateľ / Adresát", 
            help_text = "Uveďte adresáta. <strong>Netreba vypĺňať, ak je vyplnené pole Súvisiaca položka</strong>.",
            blank = True,
            max_length=200)
    inout = models.CharField("Prijatý / odoslaný",
            max_length=20, choices=InOut.choices, null=True)
    datum = models.DateField('Dátum prijatia / odoslania',
            help_text = "Dátum prijatia / odoslania dokumentu",
            null = True,
            )
    #odosielatel not used
    odosielatel = models.CharField("xTyp dokumentu", 
            max_length=200,
            blank = True)
    #url not used
    url = models.URLField('URL', 
            help_text = "Zadajte URL.",
            blank = True)
    sposob = models.CharField("Spôsob doručenia",
            help_text = "Zvoľte spôsob, akým bol dokument prijatý/doručený",
            max_length=20, choices=SposobDorucenia.choices, null=True)
    vec = models.CharField("Popis", 
            help_text = "Stručne popíšte obsah, napr. 'Podpísaná zmluva'",
            max_length=200)
    naspracovanie = models.CharField("Na spracovanie", 
            help_text = "Uveďte meno osoby, ktorej bol <strong>prijatý dokument</strong> daný na vybavenie. Pri odosielanom dokumente vložte pomlčku '-'.",
            max_length=50,
            null = True)
    #pozor: prehodené popisy polí prijalodoslal a zaznamvytvoril
    prijalodoslal = models.CharField("Záznam vytvoril", 
            help_text = "Meno používateľa, ktorý záznam v denníku vytvoril (vypĺňané automaticky)",
            max_length=50,
            blank = True)
    zaznamvytvoril = models.CharField("Prijal/odoslal", 
            help_text = "Meno používateľa, ktorý zaznamenal prijatie / odoslanie zásielky (vypĺňané automaticky).",
            max_length=50,
            blank = True)
    datumvytvorenia = models.DateField("Dátum vytvorenia záznamu",
            help_text = "Dátum vytvorenia záznamu (vypĺňané automaticky)",
            null = True)
    
    #poznamka not used
    poznamka = models.CharField("Poznámka", max_length=200, blank=True)

    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Dokument'
        verbose_name_plural = 'Prijaté a odoslané dokumenty'
    def __str__(self):
        return(self.cislo)
