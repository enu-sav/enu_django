
from django import forms
from ipdb import set_trace as trace
from .models import OsobaAutor, ZmluvaAutor, PlatbaAutorskaSumar, OsobaGrafik, ZmluvaGrafik, VytvarnaObjednavkaPlatba
from dennik.models import Dokument, SposobDorucenia, TypDokumentu
from dennik.forms import nasledujuce_cislo
from django.core.exceptions import ValidationError
from django.contrib import messages #import messages
import re

# Pridať dodatočné pole popis_zmeny, použije sa ako change_reason v SimpleHistoryAdmin
class PopisZmeny(forms.ModelForm):
    popis_zmeny = forms.CharField(widget=forms.TextInput(attrs={'size':80}))
    def save(self, commit=True):
        popis_zmeny = self.cleaned_data.get('popis_zmeny', None)
        # Get the form instance so I can write to its fields
        instance = super(PopisZmeny, self).save(commit=commit)
        # this writes the processed data to the description field
        instance._change_reason = popis_zmeny
        return super(PopisZmeny, self).save(commit=commit)
    class Meta:
        abstract = True

class OsobaAutorForm(PopisZmeny):
    class Meta:
        model = OsobaAutor
        fields = "__all__"

class OsobaGrafikForm(PopisZmeny):
    class Meta:
        model = OsobaGrafik
        fields = "__all__"

class ZmluvaForm(PopisZmeny):
    # Skontrolovať platnost a keď je všetko OK, spraviť záznam do denníka
    def clean(self):
        zo_name = ZmluvaAutor._meta.get_field('zmluva_odoslana').verbose_name
        zv_name = ZmluvaAutor._meta.get_field('zmluva_vratena').verbose_name
        vs_name = ZmluvaAutor._meta.get_field('vygenerovana_subor').verbose_name
        try:
            #kontrola
            if 'zmluva_odoslana' in self.changed_data and 'zmluva_vratena' in self.changed_data:
                raise ValidationError(f"Dátum do '{zo_name}' nemožno zadať spolu s '{zv_name}'.")
            if 'zmluva_odoslana' in self.changed_data:
                if self.instance.vygenerovana_subor:   # súbor zmluvy už existuje
                    vec = f"Zmluva {self.instance.cislo} autorovi na podpis"
                    cislo = nasledujuce_cislo(Dokument)
                    dok = Dokument(
                        cislo = cislo,
                        cislopolozky = self.instance.cislo,
                        datumvytvorenia = self.cleaned_data['zmluva_odoslana'],
                        typdokumentu = TypDokumentu.AZMLUVA,
                        adresat = self.instance.zmluvna_strana,
                        vec = f'<a href="{self.instance.vygenerovana_subor.url}">{vec}</a>',
                        prijalodoslal=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                    )
                    dok.save()
                    messages.warning(self.request, f"Do denníka bol pridaný záznam č. {cislo} '{vec}'")
                    return self.cleaned_data
                else:
                    raise ValidationError(f"Pole '{zo_name} možno vyplniť až po vygenerovaní súboru '{vt_name}'. ")
        except ValidationError as ex:
            raise ex

class ZmluvaAutorForm(ZmluvaForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        # do Admin treba pridať metódu get_form
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            nasledujuce = nasledujuce_cislo(ZmluvaAutor)
            self.fields[polecislo].help_text = f"Zadajte číslo novej autorskej zmluvy v tvare {ZmluvaAutor.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce} bolo určené na základe čísel existujúcich zmlúv ako nasledujúce v poradí."
            self.initial[polecislo] = nasledujuce

    class Meta:
        model = ZmluvaAutor
        fields = "__all__"
        fields = ['cislo', 'stav_zmluvy', 'zmluva_odoslana', 'zmluva_vratena', 'zmluvna_strana',
            'honorar_ah', 'url_zmluvy', 'datum_zverejnenia_CRZ']

class ZmluvaGrafikForm(ZmluvaForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        # do Admin treba pridať metódu get_form
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            nasledujuce = nasledujuce_cislo(ZmluvaGrafik)
            self.fields[polecislo].help_text = f"Zadajte číslo novej výtvarnej zmluvy v tvare {ZmluvaGrafik.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce} bolo určené na základe čísel existujúcich zmlúv ako nasledujúce v poradí."
            self.initial[polecislo] = nasledujuce

    class Meta:
        model = ZmluvaGrafik
        fields = "__all__"
        fields = ['cislo', 'stav_zmluvy', 'zmluva_odoslana', 'zmluva_vratena', 'zmluvna_strana',
            'url_zmluvy', 'datum_zverejnenia_CRZ']

class VytvarnaObjednavkaPlatbaForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            nasledujuce = nasledujuce_cislo(VytvarnaObjednavkaPlatba)
            self.fields[polecislo].help_text = f"Zadajte číslo novej objednávky v tvare {VytvarnaObjednavkaPlatba.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce} bolo určené na základe čísel existujúcich výtvarných objednávok ako nasledujúce v poradí."
            self.initial[polecislo] = nasledujuce

class PlatbaAutorskaSumarForm(PopisZmeny):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        # do Admin treba pridať metódu get_form
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

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
                cislo = nasledujuce_cislo(Dokument)
                vec = f"Podklady na vyplatenie aut. honorárov za {self.instance.obdobie}"
                if self.instance.vyplatit_ths:   # súbor existuje
                    dok = Dokument(
                        cislo = cislo,
                        datum = self.cleaned_data['podklady_odoslane'],
                        odosielatel = str(self.instance),
                        adresat = "Účtovník TSH", 
                        vec = f'<a href="{self.instance.vyplatit_ths.url}">{vec}</a>, hárok ''Na vyplatenie''',
                        prijalodoslal=self.request.user.username,
                        sposob = SposobDorucenia.MAIL
                    )
                    dok.save()
                    messages.warning(self.request, f"Do denníka bol pridaný záznam č. {cislo} '{vec}'")
                    return self.cleaned_data
                else:
                    raise ValidationError(f"Pole '{po_name} možno vyplniť až po vygenerovaní súboru '{vt_name}'. ")
            #na_vyplatenie_odoslane a kryci_list_odoslany možno zaznamenať naraz
            if 'na_vyplatenie_odoslane' in self.changed_data or 'kryci_list_odoslany' in self.changed_data:
                nv_dok=None
                klo_dok=None
                nv_cislo=None  #čislo dokumentu, treba inkrementovať, ak boli zadané oba dátumy
                if 'na_vyplatenie_odoslane' in self.changed_data:
                    nv_vec = f"Finálny prehľad vyplácania aut. honorárov za obdobie {self.instance.obdobie}"
                    if self.instance.vyplatene:   # súbor existuje
                        nv_cislo = nasledujuce_cislo(Dokument)
                        nv_dok = Dokument(
                            cislo = nv_cislo,
                            datum = self.cleaned_data['na_vyplatenie_odoslane'],
                            odosielatel = str(self.instance),
                            adresat = "Účtovník TSH", 
                            vec = f'<a href="{self.instance.vyplatene.url}">{nv_vec}</a>", hárok ''Na vyplatenie''',
                            prijalodoslal=self.request.user.username,
                            sposob = SposobDorucenia.MAIL
                        )
                    else:
                        raise ValidationError(f"Pole '{nv_name} možno vyplniť až po vygenerovaní súboru '{v_name}'. ")
                if 'kryci_list_odoslany' in self.changed_data:
                    if nv_cislo:
                        #inkrementovať o 1
                        rr,cc=re.findall(r"D-([0-9]*)-0*([0-9]*)",nv_cislo)[0]
                        klo_cislo = "D-%s-%03d"%(rr,int(cc)+1)
                    else:
                        klo_cislo = nasledujuce_cislo(Dokument)
                    klo_vec = f"Krycí list vyplácania aut. honorárov  za obdobie {self.instance.obdobie}"
                    if self.instance.vyplatene:   # súbor existuje
                        klo_dok = Dokument(
                            cislo = klo_cislo,
                            datum = self.cleaned_data['kryci_list_odoslany'],
                            odosielatel = str(self.instance),
                            adresat = "Účtovník TSH", 
                            vec = f'<a href="{self.instance.vyplatene.url}">{klo_vec}</a>", hárok ''Krycí list''',
                            prijalodoslal=self.request.user.username,
                            sposob = SposobDorucenia.IPOSTA
                        )
                    else:
                        raise ValidationError(f"Pole '{klo_name} možno vyplniť až po vygenerovaní súboru '{v_name}'. ")
                if nv_dok: 
                    nv_dok.save()
                    messages.warning(self.request, f"Do denníka bol pridaný záznam č. {nv_cislo} '{nv_vec}'")
                if klo_dok: 
                    klo_dok.save()
                    messages.warning(self.request, f"Do denníka bol pridaný záznam č. {klo_cislo} '{klo_vec}'")
                return self.cleaned_data
        except ValidationError as ex:
            raise ex

    class Meta:
        model = PlatbaAutorskaSumar
        fields = "__all__"
