
from django import forms
from ipdb import set_trace as trace
from .models import PrijataFaktura, Objednavka

class ObjednavkaForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not 'cislo' in self.initial:
            nasledujuce = Objednavka.nasledujuce_cislo()
            self.fields['cislo'].help_text = f"Zadajte číslo novej objednávky v tvare {Objednavka.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce} bolo určené na základe čísel existujúcich objednávok ako nasledujúce v poradí."
            self.initial['cislo'] = nasledujuce

class PrijataFakturaForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not 'cislo' in self.initial:
            nasledujuce = PrijataFaktura.nasledujuce_cislo()
            self.fields['cislo'].help_text = f"Zadajte číslo novej faktúry v tvare {PrijataFaktura.oznacenie}-RRRR-NNN alebo v prípade trvalej platby uveďte 'trvalá platba'. Predvolené číslo '{nasledujuce} bolo určené na základe čísiel existujúcich faktúr ako nasledujúce v poradí.",
            self.initial['cislo'] = nasledujuce

class AutorskeZmluvyForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['zdroj'] = 1       #111
        self.initial['program'] = 1     #Ostatné
        self.initial['zakazka'] = 1     #Beliana
        self.initial['ekoklas'] = 58    #633018	Licencie
