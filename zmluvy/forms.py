
from django import forms
from ipdb import set_trace as trace
from .models import OsobaAutor, ZmluvaAutor, PlatbaAutorskaSumar
from dennik.models import Dokument, SposobDorucenia
from dennik.forms import nasledujuce_cislo
from django.core.exceptions import ValidationError
import re

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
        polecislo = "cislo_zmluvy"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            nasledujuce = ZmluvaAutor.nasledujuce_cislo()
            self.fields[polecislo].help_text = f"Zadajte číslo novej autorskej zmluvy v tvare {ZmluvaAutor.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce} bolo určené na základe čísel existujúcich zmlúv ako nasledujúce v poradí."
            self.initial[polecislo] = nasledujuce

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
    popis_zmeny = forms.CharField(widget=forms.TextInput(attrs={'size':80}))

    # Skontrolovať platnost a keď je všetko OK, spraviť záznam do denníka
    def clean(self):
        po_name = PlatbaAutorskaSumar._meta.get_field('podklady_odoslane').verbose_name
        nvo_name = PlatbaAutorskaSumar._meta.get_field('na_vyplatenie_odoslane').verbose_name
        klo_name = PlatbaAutorskaSumar._meta.get_field('kryci_list_odoslany').verbose_name
        vt_name = PlatbaAutorskaSumar._meta.get_field('vyplatit_ths').verbose_name
        v_name = PlatbaAutorskaSumar._meta.get_field('vyplatene').verbose_name
        try:
            #kontrola
            if 'podklady_odoslane' in self.changed_data and ('kryci_list_odoslany' in self.changed_data or 'na_vyplatenie_odoslane' in self.changed_data):
                raise ValidationError(f"Dátum do '{po_name}' nemožno zadať spolu s '{nvo_name}' a '{klo_name}'.")
            if 'podklady_odoslane' in self.changed_data:
                if self.instance.vyplatit_ths:   # súbor existuje
                    dok = Dokument(
                        cislo = nasledujuce_cislo(Dokument),
                        datum = self.cleaned_data['podklady_odoslane'],
                        odosielatel = str(self.instance),
                        adresat = "Účtovník TSH", 
                        vec = "Podklady na vyplatenie aut. honorárov",
                        sposob = SposobDorucenia.MAIL
                    )
                    dok.save()
                    return self.cleaned_data
                else:
                    raise ValidationError(f"Pole '{po_name} možno vyplniť až po vygenerovaní súboru '{vt_name}'. ")
            #na_vyplatenie_odoslane a kryci_list_odoslany možno zaznamenať naraz
            if 'na_vyplatenie_odoslane' in self.changed_data or 'kryci_list_odoslany' in self.changed_data:
                nv_dok=None
                klo_dok=None
                cislo=None  #čislo dokumentu, treba inkrementovať, ak boli zadané oba dátumy
                if 'na_vyplatenie_odoslane' in self.changed_data:
                    if self.instance.vyplatene:   # súbor existuje
                        cislo = nasledujuce_cislo(Dokument)
                        nv_dok = Dokument(
                            cislo = cislo,
                            datum = self.cleaned_data['na_vyplatenie_odoslane'],
                            odosielatel = str(self.instance),
                            adresat = "Účtovník TSH", 
                            vec = "Finálny prehľad vyplácania aut. honorárov",
                            sposob = SposobDorucenia.MAIL
                        )
                    else:
                        raise ValidationError(f"Pole '{nv_name} možno vyplniť až po vygenerovaní súboru '{v_name}'. ")
                if 'kryci_list_odoslany' in self.changed_data:
                    if cislo:
                        #inkrementovať o 1
                        rr,cc=re.findall(r"D-([0-9]*)-0*([0-9]*)",cislo)[0]
                        cislo = "D-%s-%03d"%(rr,int(cc)+1)
                    else:
                        cislo = nasledujuce_cislo(Dokument),
                    if self.instance.vyplatene:   # súbor existuje
                        klo_dok = Dokument(
                            cislo = cislo,
                            datum = self.cleaned_data['kryci_list_odoslany'],
                            odosielatel = str(self.instance),
                            adresat = "Účtovník TSH", 
                            vec = "Krycí list vyplácania aut. honorárov",
                            sposob = SposobDorucenia.IPOSTA
                        )
                    else:
                        raise ValidationError(f"Pole '{klo_name} možno vyplniť až po vygenerovaní súboru '{v_name}'. ")
                    if nv_dok: nv_dok.save()
                    if klo_dok: klo_dok.save()
                    return self.cleaned_data
        except ValidationError as ex:
            raise ex

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
