from django.db import models
from simple_history.models import HistoricalRecords
from django.core.exceptions import ValidationError
from ipdb import set_trace as trace
import re

class InOut(models.TextChoices):
    PRIJATY = 'prijaty', 'Príjem'
    ODOSLANY = 'odoslany', 'Odoslanie'

class TypDokumentu(models.TextChoices):
    AZMLUVA = 'autorskazmluva', 'Autorská zmluva'
    VZMLUVA = 'vytvarnazmluva', 'Výtvarná zmluva'
    VOBJEDNAVKA = 'vobjednavka', 'Výtvarná objednávka'
    OBJEDNAVKA = 'objednavka', 'Objednávka'
    FAKTURA = 'faktura', 'Faktúra'
    PSTRAVNE = 'pstravne', 'Príspevok na stravné'
    ZMLUVA = 'zmluva', 'Zmluva'
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
            help_text = "Ak je to relevantné, uveďte číslo súvisiacej položky v Djangu (autorskej zmluvy, dohody) v tvare X-RRRR-NNN, inak vložte pomlčku '-'.<br />V prípade <strong>prijatej faktúry</strong> najskôr vytvorte novú prijatú faktúru a následne len upravte záznam pošty, ktorý sa tým vytvorí.<br />V prípade <strong>odosielaných dokumentov</strong>, ktoré sa vytvárajú v Djangu, už pre ne môže v tomto denníku existovať záznam. Skontrolujte to, a ak záznam existuje, použite ten.", 
            max_length=200)
    typdokumentu = models.CharField("Typ dokumentu",
            max_length=20, choices=TypDokumentu.choices, 
            help_text = "Uveďte typ dokumentu. <strong>Netreba vypĺňať, ak je v poli Súvisiaca položka uvedená položka databázy v tvare X-RRRR-NNN</strong>.",
            blank = True,
            null=True)
    adresat = models.CharField("Odosielateľ / Adresát", 
            help_text = "Uveďte adresáta. <br />Netreba vypĺňať, ak je v poli Súvisiaca položka uvedená položka databázy v tvare X-RRRR-NNN.<br />Ak už je pole v prípade odosielania dokumentu vopred vyplnené, adresáta ponechajte.",
            blank = True,
            max_length=200)
    inout = models.CharField("Príjem / odoslanie",
            max_length=20, choices=InOut.choices, null=True)
    datum = models.DateField('Dátum príjmu / odoslania',
            help_text = "Dátum príjmu / odoslania dokumentu",
            null = True,
            )
    #odosielatel not used
    #odosielatel = models.CharField("xTyp dokumentu", 
            #max_length=200,
            #blank = True)
    #url not used
    #url = models.URLField('URL', 
            #help_text = "Zadajte URL.",
            #blank = True)
    sposob = models.CharField("Spôsob doručenia",
            help_text = "Zvoľte spôsob, akým bol dokument prijatý/doručený",
            max_length=20, choices=SposobDorucenia.choices, null=True)
    vec = models.CharField("Popis", 
            help_text = "Stručne popíšte obsah, napr. 'Podpísaná zmluva'",
            max_length=200)
    naspracovanie = models.CharField("Na spracovanie", 
            help_text = "<strong>Ak ide o prijatý dokument</strong>, uveďte meno osoby, ktorej bol daný na vybavenie. Pri odosielanom dokumente vypĺňať netreba.",
            max_length=50,
            blank = True,
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
    
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Prijatá alebo odoslaná pošta'
        verbose_name_plural = 'Denník prijatej a odoslanej pošty'
    def __str__(self):
        return(self.cislo)
