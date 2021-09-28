
from django import forms
from ipdb import set_trace as trace
from .models import OsobaAutor, ZmluvaAutor, PlatbaAutorskaSumar

# Pridať dodatočné pole popis_zmeny, použije sa ako change_reason v SimpleHistoryAdmin
class OsobaAutorForm(forms.ModelForm):
    #popis_zmeny = forms.CharField()
    popis_zmeny = forms.CharField(widget=forms.TextInput(attrs={'size':80}))
    def save(self, commit=True):
        popis_zmeny = self.cleaned_data.get('popis_zmeny', None)
        # Get the form instance so I can write to its fields
        instance = super(OsobaAutorForm, self).save(commit=commit)
        # this writes the processed data to the description field
        instance._change_reason = popis_zmeny
        return super(OsobaAutorForm, self).save(commit=commit)

    class Meta:
        model = OsobaAutor
        fields = "__all__"

# Pridať dodatočné pole popis_zmeny, použije sa ako change_reason v SimpleHistoryAdmin
class ZmluvaAutorForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ak zmluva existuje 'cislo_zmluvy' je nastavené ako readonly v admin.py. Vtedy nie je v self.fields
        # Preto testujeme self.fields a nie self.initial (to nestačí)
        if 'cislo_zmluvy' in self.fields:
            nasledujuce = ZmluvaAutor.nasledujuce_cislo()
            self.fields['cislo_zmluvy'].help_text = f"Zadajte číslo novej autorskej zmluvy v tvare {ZmluvaAutor.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce} bolo určené na základe čísel existujúcich zmlúv ako nasledujúce v poradí."
            self.initial['cislo_zmluvy'] = nasledujuce

    popis_zmeny = forms.CharField(widget=forms.TextInput(attrs={'size':80}))
    def save(self, commit=True):
        popis_zmeny = self.cleaned_data.get('popis_zmeny', None)
        # Get the form instance so I can write to its fields
        instance = super(ZmluvaAutorForm, self).save(commit=commit)
        # this writes the processed data to the description field
        instance._change_reason = popis_zmeny
        return super(ZmluvaAutorForm, self).save(commit=commit)

    class Meta:
        model = ZmluvaAutor
        fields = "__all__"


# Pridať dodatočné pole popis_zmeny, použije sa ako change_reason v SimpleHistoryAdmin
class PlatbaAutorskaSumarForm(forms.ModelForm):
    #popis_zmeny = forms.CharField()
    popis_zmeny = forms.CharField(widget=forms.TextInput(attrs={'size':80}))
    def save(self, commit=True):
        popis_zmeny = self.cleaned_data.get('popis_zmeny', None)
        # Get the form instance so I can write to its fields
        instance = super(PlatbaAutorskaSumarForm, self).save(commit=commit)
        # this writes the processed data to the description field
        instance._change_reason = popis_zmeny
        return super(PlatbaAutorskaSumarForm, self).save(commit=commit)

    class Meta:
        model = PlatbaAutorskaSumar
        fields = "__all__"
