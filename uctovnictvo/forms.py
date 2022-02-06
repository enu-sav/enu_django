
from django.contrib import messages
from django import forms
from django.core.exceptions import ValidationError
from ipdb import set_trace as trace
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import PrijataFaktura, Objednavka, PrispevokNaStravne, DoPC, DoVP, DoBPS, PlatovyVymer, VyplacanieDohod
from dennik.models import Dokument, SposobDorucenia, TypDokumentu, InOut
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

class PopisZmeny(forms.ModelForm):
    popis_zmeny = forms.CharField(widget=forms.TextInput(attrs={'size':80}))
    def save(self, commit=True):
        popis_zmeny = self.cleaned_data.get('popis_zmeny', None)
        # Get the form instance so I can write to its fields
        instance = super(PopisZmeny, self).save(commit=commit)
        # this writes the processed data to the description field
        instance._change_reason = popis_zmeny
        return super(PopisZmeny, self).save(commit=commit)

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
        # do Admin treba pridať metódu get_form
        self.request = kwargs.pop('request', None)
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

    # Skontrolovať platnost a keď je všetko OK, spraviť záznam do denníka
    def clean(self):
        if 'cislo' in self.changed_data:
            if not (self.cleaned_data['cislo'][:2] == PrijataFaktura.oznacenie or self.cleaned_data['cislo'] == PrijataFaktura.tp_text):
                raise ValidationError({"cislo": "Nesprávne číslo. Zadajte číslo novej faktúry v tvare {PrijataFaktura.oznacenie}-RRRR-NNN alebo v prípade trvalej platby uveďte 'trvalá platba'"})
        try:
            #pole dane_na_uhradu možno vyplniť až po vygenerovani platobného príkazu akciou 
            #"Vytvoriť platobný príkaz a krycí list pre THS"
            if 'dane_na_uhradu' in self.changed_data:
                vec = f"Platobný príkaz na THS {self.instance.cislo} na vyplatenie"
                cislo = nasledujuce_cislo(Dokument)
                dok = Dokument(
                    cislo = cislo,
                    cislopolozky = self.instance.cislo,
                    datumvytvorenia = self.cleaned_data['dane_na_uhradu'],
                    typdokumentu = TypDokumentu.FAKTURA,
                    inout = InOut.ODOSLANY,
                    adresat = "THS",
                    vec = f'<a href="{self.instance.platobny_prikaz.url}">{vec}</a>',
                    prijalodoslal=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                )
                dok.save()
                messages.warning(self.request, 
                    format_html(
                        'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>, treba v ňom doplniť údaje o odoslaní.',
                        mark_safe(f'<a href="/admin/dennik/dokument/{dok.id}/change/">{cislo}</a>'),
                        vec
                        )
            )
        except ValidationError as ex:
            raise ex
        return self.cleaned_data

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
        self.initial['ekoklas'] = 97    #637027 - Odmeny zamestnancov mimopracovného pomeru
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
        self.initial['ekoklas'] = 97    #637027 - Odmeny zamestnancov mimopracovného pomeru
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields:
            if not polecislo in self.initial:
                nasledujuce = nasledujuce_cislo(DoVP)
                self.fields[polecislo].help_text = f"Zadajte číslo novej DoVP v tvare {DoVP.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce} bolo určené na základe čísiel existujúcich DoVP ako nasledujúce v poradí."
                self.initial[polecislo] = nasledujuce
            else:
                self.fields[polecislo].help_text = f"Číslo faktúry v tvare {DoVP.oznacenie}-RRRR-NNN."

class DoBPSForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['zdroj'] = 1       #111
        self.initial['program'] = 1     #Ostatné
        self.initial['zakazka'] = 1     #Beliana
        self.initial['ekoklas'] = 97    #637027 - Odmeny zamestnancov mimopracovného pomeru
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields:
            if not polecislo in self.initial:
                nasledujuce = nasledujuce_cislo(DoBPS)
                self.fields[polecislo].help_text = f"Zadajte číslo novej DoBPS v tvare {DoBPS.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce} bolo určené na základe čísiel existujúcich DoBPS ako nasledujúce v poradí."
                self.initial[polecislo] = nasledujuce
            else:
                self.fields[polecislo].help_text = f"Číslo faktúry v tvare {DoBPS.oznacenie}-RRRR-NNN."

class PlatovyVymerForm(PopisZmeny):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['zdroj'] = 1       #111
        self.initial['program'] = 1     #Ostatné
        self.initial['zakazka'] = 2     #11010001 spol. zák.
        self.initial['ekoklas'] = 18    #611 - Tarifný plat, osobný plat, základný plat, funkčný plat, hodnostný plat, plat, vrátane ich náhrad
    class Meta:
        model = PlatovyVymer
        fields = "__all__"
        field_order = ["cislo_zamestnanca", "zamestnanec", "suborvymer", "datum_od", "datum_do", "tarifny_plat", "osobny_priplatok", "funkcny_priplatok", "platova_trieda", "platovy_stupen", "datum_postup", "praxroky", "praxdni", "zamestnanieroky", "zamestnaniedni", "popis_zmeny"]

class VyplacanieDohodForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        # do Admin treba pridať metódu get_form
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    # Skontrolovať platnost a keď je všetko OK, spraviť záznam do denníka
    def clean(self):
        d_name = VyplacanieDohod._meta.get_field('dohoda').verbose_name
        dv_name = VyplacanieDohod._meta.get_field('datum_vyplatenia').verbose_name
        try:
            if not self.instance.dohoda and not 'dohoda' in self.changed_data:
                raise ValidationError("")
            if not self.instance.datum_vyplatenia and not 'datum_vyplatenia' in self.changed_data:
                raise ValidationError("")
            #kontrola
            cislo = nasledujuce_cislo(Dokument)
            dohoda = self.cleaned_data['dohoda']
            vec = f"Podklady na vyplatenie dohody {dohoda}"
            if type(dohoda) == DoVP:
                dtype="dovp"
            elif type(dohoda) == DoPC:
                dtype="dopc"
            elif type(dohoda) == DoBPS:
                dtype="dobps"
            dok = Dokument(
                cislo = cislo,
                datum = self.cleaned_data['datum_vyplatenia'],
                odosielatel = f"Vyplatenie dohody {dohoda}",
                adresat = "Mzdové oddelenie", 
                vec = f'Podklady na vyplatenie dohody <a href="/admin/uctovnictvo/{dtype}/{dohoda.id}/change/">{dohoda}</a>',
                prijalodoslal=self.request.user.username,
                sposob = SposobDorucenia.IPOSTA
            )
            dok.save()
            messages.warning(self.request, f"Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {cislo} '{vec}'")
            return self.cleaned_data
        except ValidationError as ex:
            raise ex
