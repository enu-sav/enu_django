
from django import forms
from ipdb import set_trace as trace
from .models import PrijataFaktura, Objednavka

class ObjednavkaForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not 'cislo' in self.initial:
            self.initial['cislo'] = Objednavka.nasledujuce_cislo()

class PrijataFakturaForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not 'cislo' in self.initial:
            self.initial['cislo'] = PrijataFaktura.nasledujuce_cislo()

class AutorskeZmluvyForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['zdroj'] = 1       #111
        self.initial['program'] = 1     #Ostatné
        self.initial['zakazka'] = 1     #Beliana
        self.initial['ekoklas'] = 58    #633018	Licencie
