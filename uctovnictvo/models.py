from django.db import models

#ak sa doplni stav pred 'PODPISANA_ENU', treba doplniť test vo funkcii vytvorit_subory_zmluvy
class Zdroj(models.TextChoices):
    Z111 = "z111", "111"    #štátny rozpočet
    Z46 = "z46", "46"       #xxx
    Z42 = "z42", "42"       #yyy

class Program(models.TextChoices):
    _087060J = "087060J", "087060J"
    _0EK1102 = "0EK1102", "0EK1102"
    _0EK1103 = "0EK1103", "0EK1103"

class Zakazka(models.TextChoices):
    BELIANA = "beliana", "Beliana"
    OSTATNE = "ostatne", "Ostatne"

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
    #zdroj = models.CharField("Zdroj", 
            #help_text = "Zadajte zdroj - 111, 46 alebo 42", 
            #max_length=10, null=True, blank=True)
    zdroj = models.CharField("Zdroj", 
            help_text = "Zadajte zdroj - 111, 46 alebo 42", 
            max_length = 20,
            choices = Zdroj.choices)
    #program = models.CharField("Program", 
            #help_text = "Zadajte program - 087060J, 0EK1102 alebo 0EK1103",
            #max_length=10, null=True, blank=True)
    program = models.CharField("Program", 
            help_text = "Zadajte program - 087060J, 0EK1102 alebo 0EK1103",
            max_length = 20,
            choices = Program.choices)
    zakazka = models.CharField("Zákazka", 
            help_text = "Zadajte zákazku - Beliana alebo Ostatné",
            max_length = 20,
            choices = Zakazka.choices)
    ekoklas = models.ForeignKey(EkonomickaKlasifikacia, on_delete=models.PROTECT, related_name='transakcie')    
    class Meta:
        verbose_name = 'Transakcia'
        verbose_name_plural = 'Transakcie'
    
