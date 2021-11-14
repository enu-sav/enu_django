from django.db import models
from simple_history.models import HistoricalRecords

# Create your models here.
class Dokument(models.Model):
    oznacenie = "D"    #v čísle dokument, D-2021-123
    cislo = models.CharField("Číslo dokumentu", max_length=50)
    datum = models.DateField('Dátum')
    odosielatel = models.CharField("Odosielateľ", max_length=200)
    adresat = models.CharField("Adresát", max_length=200)
    vec = models.CharField("Vec", max_length=200)
    poznamka = models.CharField("Poznámka", max_length=200, blank=True)

    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Dokument'
        verbose_name_plural = 'Prijaté a odoslané dokumenty'
    def __str__(self):
        return(self.cislo)
