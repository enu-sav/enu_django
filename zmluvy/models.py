import datetime
from django.db import models
from django.utils import timezone

# Create your models here.
class Osoba(models.Model):
    rs_uid = models.IntegerField("Uid v RS")
    rs_login = models.CharField("Login v RS", max_length=100)
    email = models.CharField("Email", max_length=200)
    titul_pred_menom = models.CharField("Titul pred menom", max_length=100, blank=True)
    meno = models.CharField("Meno", max_length=200)
    priezvisko = models.CharField("Priezvisko", max_length=200)
    titul_za_menom = models.CharField("Titul za menom", max_length=100, blank=True)
    posobisko = models.CharField("Pôsobisko", max_length=200, blank=True)
    datum_pridania = models.DateTimeField('Dátum pridania')
    datum_aktualizacie = models.DateTimeField('Dátum aktualizácie')
    #pub_date = models.DateTimeField('date published')

    def __str__(self):
        return self.rs_login
    def nedavno_pridane(self):
        return self.datum_aktualizacie >= timezone.now() - datetime.timedelta(days=1)

#1057	TrnkaAlfred	atrnka@truni.sk	prof. RNDr.	Alfréd	Trnka	PhD.	1729
#   oo = Osoba(rs_uid = 1057, rs_login = "TrnkaAlfred", email = "atrnka@truni.sk", titul_pred_menom = "RNDr.", meno = "Alfréd", priezvisko = "Trnka", titul_za_menom = "PhD.", posobisko = "Truni, Trenčín")

#1062	AstalosBoris	boris.astalos@SNM.sk		Boris	Astaloš		40/2019
#   oo = Osoba(rs_uid = 1062, rs_login = "AstalosBoris", email = "boris.astalos@SNM.sk", meno = "Boris", priezvisko = "Astaloš", posobisko = "Slovenské národné múzeum, Bratislava")
#z=Zmluva(zmluvna_strana=oo, cislo_zmluvy="40/2019")

    

class Zmluva(models.Model):
    zmluvna_strana = models.ForeignKey(Osoba, on_delete=models.CASCADE)
    cislo_zmluvy = models.CharField("Číslo zmluvy", max_length=50)
    datum_pridania = models.DateTimeField('Dátum pridania')
    datum_aktualizacie = models.DateTimeField('Dátum aktualizácie')

    def __str__(self):
        return self.cislo_zmluvy
    def nedavno_aktualizovane(self):
        return self.datum_aktualizacie >= timezone.now() - datetime.timedelta(days=1)

