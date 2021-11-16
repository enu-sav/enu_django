from django.db import models
from simple_history.models import HistoricalRecords

class SposobDorucenia(models.TextChoices):
    POSTA = 'posta', 'Pošta'
    IPOSTA = 'iposta', 'Interná pošta'
    MAIL = 'mail', 'E-mail'
    OSOBNE = 'osobne', 'Osobne'

# Create your models here.
class Dokument(models.Model):
    oznacenie = "D"    #v čísle dokument, D-2021-123
    cislo = models.CharField("Číslo dokumentu", max_length=50)
    datum = models.DateField('Dátum')
    odosielatel = models.CharField("Odosielateľ", max_length=200)
    adresat = models.CharField("Adresát", max_length=200)
    url = models.URLField('URL', 
            help_text = "Zadajte URL.",
            blank = True)
    sposob = models.CharField("Spôsob doručenia",
            help_text = "Zvoľte spôsob, akým bol dokument prijatý/doručený",
            max_length=20, choices=SposobDorucenia.choices, null=True, blank=True) 
    vec = models.CharField("Vec", max_length=200)
    
    poznamka = models.CharField("Poznámka", max_length=200, blank=True)

    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Dokument'
        verbose_name_plural = 'Prijaté a odoslané dokumenty'
    def __str__(self):
        return(self.cislo)
