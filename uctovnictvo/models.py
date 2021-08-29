from django.db import models

#záznam histórie
#https://django-simple-history.readthedocs.io/en/latest/admin.html
from simple_history.models import HistoricalRecords

class Zdroj(models.Model):
    kod = models.CharField("Kód", 
            help_text = "Zadajte kód zdroja - napr. 111, 46 alebo 42", 
            max_length=20)
    popis = models.CharField("Popis", 
            help_text = "Popíšte zdroj",
            max_length=100)
    def __str__(self):
        return self.kod
    class Meta:
        verbose_name = 'Zdroj'
        verbose_name_plural = 'Zdroje'

class Program(models.Model):
    kod = models.CharField("Kód", 
            help_text = "Zadajte kód programu - napr. 087060J, 0EK1102 alebo 0EK1103",
            max_length=20)
    popis = models.CharField("Popis", 
            help_text = "Popíšte program",
            max_length=100)
    def __str__(self):
        return self.kod
    class Meta:
        verbose_name = 'Program'
        verbose_name_plural = 'Programy'

class TypZakazky(models.Model):
    kod = models.CharField("Kód", 
            help_text = "Zadajte kód typu zákazky, napr. Beliana alebo Ostatné",
            max_length=20)
    popis = models.CharField("Popis", 
            help_text = "Popíšte typ zákazky",
            max_length=100)
    def __str__(self):
        return self.kod
    class Meta:
        verbose_name = 'Typ zákazky'
        verbose_name_plural = 'Typy zákazky'

class EkonomickaKlasifikacia(models.Model):
    kod = models.CharField("Kód", 
            help_text = "Zadajte kód položky/podpoložky ekonomickej klasifikácie napr. 614 alebo 632001 (bez medzery)",
            max_length=10)
    nazov = models.CharField("Názov", 
            help_text = "Zadajte názov položky/podpoložky ekonomickej klasifikácie napr. 'Granty a transfery'",
            max_length=100)
    def __str__(self):
        return self.kod
    class Meta:
        verbose_name = 'Ekonomická klasifikácia'
        verbose_name_plural = 'Ekonomická klasifikácia'


# Create your models here.
class Transakcia(models.Model):
    zdroj = models.ForeignKey(Zdroj, on_delete=models.PROTECT, related_name='transakcie')    
    program = models.ForeignKey(Program, 
            on_delete=models.PROTECT, 
            null=True, blank=True,
            related_name='transakcie')    
    zakazka = models.ForeignKey(TypZakazky, 
            on_delete=models.PROTECT, 
            null=True, blank=True,
            related_name='transakcie')    
    ekoklas = models.ForeignKey(EkonomickaKlasifikacia, on_delete=models.PROTECT, related_name='transakcie')    
    popis = models.CharField("Popis transakcie", 
            help_text = "Zadajte stručný popis, napr. 'SPP fa 20', 'vratenie duplicitnej platby' a podobne",
            max_length=100)
    suma = models.DecimalField("Suma v EUR", 
            help_text = "Zadajte príjmy ako kladné, výdavky ako záporné číslo",
            max_digits=8, 
            decimal_places=2, 
            default=0)
    datum = models.DateField('Dátum transakcie')
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Transakcia'
        verbose_name_plural = 'Transakcie'
    
