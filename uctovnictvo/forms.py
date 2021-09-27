
from django import forms
from .models import PrijataFaktura

#inicializácia polí
class PrijataFakturaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['cislo'] = PrijataFaktura.nasledujuce_cislo()
