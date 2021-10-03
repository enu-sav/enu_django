
from django import forms
from ipdb import set_trace as trace
from .models import PrijataFaktura, Objednavka, PrispevokNaStravne, DoPC, DoVP
from datetime import datetime
import re

# Pre triedu classname určí číslo nasledujúceho záznamu v pvare X-2021-NNN
def nasledujuce_cislo(classname):
        # zoznam faktúr s číslom "PS-2021-123" zoradený vzostupne
        ozn_rok = f"{classname.oznacenie}-{datetime.now().year}-"
        itemlist = classname.objects.filter(cislo__istartswith=ozn_rok).order_by("cislo")
        if itemlist:
            latest = itemlist.last().cislo
            nove_cislo = int(re.findall(f"{ozn_rok}([0-9]+)",latest)[0]) + 1
            return "%s%03d"%(ozn_rok, nove_cislo)
        else:
            #sme v novom roku alebo trieda este nema instanciu
            return f"{ozn_rok}001"

class ObjednavkaForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            nasledujuce = nasledujuce_cislo(Objednavka)
            self.fields[polecislo].help_text = f"Zadajte číslo novej objednávky v tvare {Objednavka.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce} bolo určené na základe čísel existujúcich objednávok ako nasledujúce v poradí."
            self.initial[polecislo] = nasledujuce

class ZmluvaForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            self.fields[polecislo].help_text = "Zadajte číslo zmluvy (naše číslo alebo číslo dodávateľa). Na jednoduché rozlíšenie viacerých zmlúv toho istého dodávateľa možno v zátvorke uviesť krátku doplnkovú informáciu, napr. '2/2018 (dodávka plynu)'"

class PrijataFakturaForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields:
            if not polecislo in self.initial:
                nasledujuce = nasledujuce_cislo(PrijataFaktura)
                self.fields[polecislo].help_text = f"Zadajte číslo novej faktúry v tvare {PrijataFaktura.oznacenie}-RRRR-NNN alebo v prípade trvalej platby uveďte 'trvalá platba'. Predvolené číslo '{nasledujuce} bolo určené na základe čísiel existujúcich faktúr ako nasledujúce v poradí."
                self.initial[polecislo] = nasledujuce
            else:
                self.fields[polecislo].help_text = f"Číslo faktúry v tvare {PrijataFaktura.oznacenie}-RRRR-NNN. V prípade trvalej platby uveďte 'trvalá platba'."

class PrispevokNaStravneForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['zdroj'] = 1       #111
        self.initial['program'] = 1     #Ostatné
        self.initial['zakazka'] = 2     #11010001 spol. zák.	Činnosti z prostriedkov SAV - rozpočet 111
        self.initial['ekoklas'] = 108   #642014 Transfery jednotlivcom
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields:
            if not polecislo in self.initial:
                nasledujuce = nasledujuce_cislo(PrispevokNaStravne)
                self.fields[polecislo].help_text = f"Zadajte číslo novej faktúry v tvare {PrispevokNaStravne.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce} bolo určené na základe čísiel existujúcich faktúr ako nasledujúce v poradí."
                self.initial[polecislo] = nasledujuce
            else:
                self.fields[polecislo].help_text = f"Číslo faktúry v tvare {PrispevokNaStravne.oznacenie}-RRRR-NNN."

class AutorskeZmluvyForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['zdroj'] = 1       #111
        self.initial['program'] = 1     #Ostatné
        self.initial['zakazka'] = 1     #Beliana
        self.initial['ekoklas'] = 58    #633018	Licencie

class DoPCForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['zdroj'] = 1       #111
        self.initial['program'] = 1     #Ostatné
        self.initial['zakazka'] = 1     #Beliana
        self.initial['ekoklas'] = 58    #633018	Licencie
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields:
            if not polecislo in self.initial:
                nasledujuce = nasledujuce_cislo(DoPC)
                self.fields[polecislo].help_text = f"Zadajte číslo novej DoPČ v tvare {DoPC.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce} bolo určené na základe čísiel existujúcich DoPČ ako nasledujúce v poradí."
                self.initial[polecislo] = nasledujuce
            else:
                self.fields[polecislo].help_text = f"Číslo faktúry v tvare {DoPC.oznacenie}-RRRR-NNN."

class DoVPForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['zdroj'] = 1       #111
        self.initial['program'] = 1     #Ostatné
        self.initial['zakazka'] = 1     #Beliana
        self.initial['ekoklas'] = 58    #633018	Licencie
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields:
            if not polecislo in self.initial:
                nasledujuce = nasledujuce_cislo(DoVP)
                self.fields[polecislo].help_text = f"Zadajte číslo novej DoVP v tvare {DoVP.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce} bolo určené na základe čísiel existujúcich DoVP ako nasledujúce v poradí."
                self.initial[polecislo] = nasledujuce
            else:
                self.fields[polecislo].help_text = f"Číslo faktúry v tvare {DoVP.oznacenie}-RRRR-NNN."
