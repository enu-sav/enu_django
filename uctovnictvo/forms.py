
from django import forms
from .models import PrijataFaktura

#inicializácia polí
class PrijataFakturaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['cislo'] = PrijataFaktura.nasledujuce_cislo()

class AutorskeZmluvyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['zdroj'] = 1       #111
        self.initial['program'] = 1     #Ostatné
        self.initial['zakazka'] = 1     #Beliana
        self.initial['ekoklas'] = 58    #633018	Licencie
