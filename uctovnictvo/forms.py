
from django.contrib import messages
from django import forms
from django.core.exceptions import ValidationError
from ipdb import set_trace as trace
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import PrijataFaktura, Objednavka, PrispevokNaStravne, DoPC, DoVP, DoBPS, PlatovyVymer, VyplacanieDohod, StavDohody, Dohoda, PravidelnaPlatba, TypPP
from dennik.models import Dokument, SposobDorucenia, TypDokumentu, InOut
from datetime import date, datetime
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
                self.fields[polecislo].help_text = f"Zadajte číslo novej faktúry v tvare {PrijataFaktura.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce} bolo určené na základe čísiel existujúcich faktúr ako nasledujúce v poradí."
                self.initial[polecislo] = nasledujuce
            else:
                self.fields[polecislo].help_text = f"Číslo faktúry v tvare {PrijataFaktura.oznacenie}-RRRR-NNN."

    # Skontrolovať platnost a keď je všetko OK, spraviť záznam do denníka
    def clean(self):
        if 'cislo' in self.changed_data:
            if not self.cleaned_data['cislo'][:2] == PrijataFaktura.oznacenie:
                raise ValidationError({"cislo": "Nesprávne číslo. Zadajte číslo novej faktúry v tvare {PrijataFaktura.oznacenie}-RRRR-NNN"})
        try:
            #pole dane_na_uhradu možno vyplniť až po vygenerovani platobného príkazu akciou 
            #"Vytvoriť platobný príkaz a krycí list pre THS"
            if 'dane_na_uhradu' in self.changed_data:
                vec = f"Platobný príkaz na THS {self.instance.cislo} na vyplatenie"
                cislo = nasledujuce_cislo(Dokument)
                dok = Dokument(
                    cislo = cislo,
                    cislopolozky = self.instance.cislo,
                    #datumvytvorenia = self.cleaned_data['dane_na_uhradu'],
                    datumvytvorenia = date.today(),
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

class PravidelnaPlatbaForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        # do Admin treba pridať metódu get_form
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields:
            if not polecislo in self.initial:
                nasledujuce = nasledujuce_cislo(PravidelnaPlatba)
                self.fields[polecislo].help_text = f"Zadajte číslo novej platby v tvare {PravidelnaPlatba.oznacenie}-RRRR-NNN'. Predvolené číslo '{nasledujuce} bolo určené na základe čísiel existujúcich platieb ako nasledujúce v poradí."
                self.initial[polecislo] = nasledujuce
            else:
                self.fields[polecislo].help_text = f"Číslo platby v tvare {PravidelnaPlatba.oznacenie}-RRRR-NNN."
        if "splatnost_datum" in self.fields:
            if not "splatnost_datum" in self.initial:
                self.fields["splatnost_datum"].help_text = f"Zadajte dátum splatnosti prvého vyplácania (obvykle v januári). Po uložení sa vytvorí záznam pre všetky opakovania pravidelnej platby do konca roka."
            else:
                self.fields["splatnost_datum"].help_text = f"Dátum splatnosti"

    # Skontrolovať platnost a keď je všetko OK, spraviť záznam do denníka
    def clean(self):
        if 'cislo' in self.changed_data:
            if not self.cleaned_data['cislo'][:2] == PravidelnaPlatba.oznacenie:
                raise ValidationError({"cislo": "Nesprávne číslo. Zadajte číslo novej platby v tvare {PravidelnaPlatba.oznacenie}-RRRR-NNN"})
        #Ak vytvárame novú platbu, doplniť platby do konca roka
        if 'typ' in self.changed_data:
            rok, poradie = re.findall(r"-([0-9]+)-([0-9]+)", self.cleaned_data['cislo'])[0]
            rok = int(rok)
            poradie = int(poradie) + 1
            # skontrolovať znamienko
            if self.cleaned_data['typ'] in [TypPP.ZALOHA_EL_ENERGIA]:   #výdavok
                if  self.cleaned_data['suma'] > 0:  self.cleaned_data['suma'] *= -1
            else:   #príjem
                if  self.cleaned_data['suma'] < 0:  self.cleaned_data['suma'] *= -1
            for mesiac in range(self.cleaned_data['splatnost_datum'].month+1, 13):
                #vyplňa sa: ['zdroj', 'zakazka', 'ekoklas', 'splatnost_datum', 'suma', 'objednavka_zmluva', 'typ']
                dup = PravidelnaPlatba(
                    zdroj = self.cleaned_data['zdroj'],
                    zakazka = self.cleaned_data['zakazka'],
                    program = self.cleaned_data['program'],
                    ekoklas = self.cleaned_data['ekoklas'],
                    suma = self.cleaned_data['suma'],
                    typ = self.cleaned_data['typ'],
                    cislo = "%s-%d-%03d"%(PravidelnaPlatba.oznacenie, rok, poradie),
                    splatnost_datum = date(rok, mesiac, self.cleaned_data['splatnost_datum'].day)
                    )
                #nepovinné
                if 'objednavka_zmluva' in self.changed_data:
                    dup.objednavka_zmluva = self.cleaned_data['objednavka_zmluva']
                poradie += 1
                dup.save()
                pass

class PrispevokNaStravneForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['zdroj'] = 1       #111
        self.initial['program'] = 4     #nealokovaný
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
        self.initial['program'] = 4     #nealokovaný
        self.initial['zakazka'] = 1     #Beliana
        self.initial['ekoklas'] = 58    #633018	Licencie

class DohodaForm(forms.ModelForm):
    # Skontrolovať platnost a keď je všetko OK, spraviť záznam do denníka
    def clean(self):
        do_name = Dohoda._meta.get_field('dohoda_odoslana').verbose_name
        try:
            if 'dohoda_odoslana' in self.changed_data and 'stav_dohody' in self.changed_data:
                if self.instance.subor_dohody and self.cleaned_data['stav_dohody'] == StavDohody.ODOSLANA_DOHODAROVI:   # súbor dohody musí existovať
                    vec = f"Dohoda {self.instance.cislo} autorovi na podpis"
                    cislo = nasledujuce_cislo(Dokument)
                    dok = Dokument(
                        cislo = cislo,
                        cislopolozky = self.instance.cislo,
                        datumvytvorenia = date.today(), 
                        typdokumentu = TypDokumentu.DoVP if type(self.instance)== DoVP else TypDokumentu.DoPC if type(self.instance) == DoPC else TypDokumentu.DoBPS,
                        inout = InOut.ODOSLANY,
                        adresat = self.instance.zmluvna_strana,
                        vec = f'<a href="{self.instance.subor_dohody.url}">{vec}</a>',
                        prijalodoslal=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                    )
                    dok.save()
                    messages.warning(self.request, f"Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {cislo} '{vec}'")
                    return self.cleaned_data
                elif not self.instance.subor_dohody:
                    raise ValidationError({"stav_dohody":f"Stav dohody možno zmeniť na '{StavDohody.ODOSLANA_DOHODAROVI.label}' až po vygenerovaní súboru dohody akciou 'Vytvoriť súbor dohody' a po jej podpísaní vedením EnÚ."})
                elif self.instance.stav_dohody != StavDohody.ODOSLANA_DOHODAROVI:
                    raise ValidationError({"stav_dohody":f"Ak bolo vyplnené pole '{do_name}', stav dohody musí byť zmenený na '{StavDohody.ODOSLANA_DOHODAROVI.label}'."})
            elif 'dohoda_odoslana' in self.changed_data and not 'stav_dohody' in self.changed_data:
                raise ValidationError({"stav_dohody":f"Ak bolo vyplnené pole '{do_name}', stav dohody musí byť zmenený na '{StavDohody.ODOSLANA_DOHODAROVI.label}'."})
            elif not 'dohoda_odoslana' in self.changed_data and 'stav_dohody' in self.changed_data and self.cleaned_data["stav_dohody"] == StavDohody.ODOSLANA_DOHODAROVI:
                #vrátiť na pôvodnú hodnotu, inak bude pole 'dohoda_odoslana' readonly
                if not self.instance.subor_dohody:
                    self.cleaned_data["stav_dohody"]=self.instance.stav_dohody
                    raise ValidationError(f"Ak chcete stav dohody zmeniť na '{StavDohody.ODOSLANA_DOHODAROVI.label}', tak najskôr treba vygenerovať súbor dohody akciou 'Vytvoriť súbor dohody'.")
                elif self.instance.stav_dohody == StavDohody.VYTVORENA:
                    self.cleaned_data["stav_dohody"]=self.instance.stav_dohody
                    raise ValidationError({"stav_dohody":f"Ak chcete stav dohody zmeniť na '{StavDohody.ODOSLANA_DOHODAROVI.label}', tak ju najskôr treba dať do stavu '{StavDohody.NAPODPIS.label}'"})
                else:
                    self.cleaned_data["stav_dohody"]=self.instance.stav_dohody
                    raise ValidationError(f"Ak chcete stav dohody zmeniť na '{StavDohody.ODOSLANA_DOHODAROVI.label}', tak treba vyplniť aj pole '{do_name}'.")
        except ValidationError as ex:
            raise ex
        if "stav_dohody" in self.cleaned_data and self.cleaned_data["stav_dohody"] == StavDohody.NOVA:
            messages.warning(self.request, f"Po vyplnení údajov treba vygenerovať súbor dohody akciou 'Vytvoriť súbor dohody'")
        elif "stav_dohody" in self.cleaned_data and self.cleaned_data["stav_dohody"] == StavDohody.VYTVORENA:
            messages.warning(self.request, f"Po aktualizácii údajov treba opakovane vygenerovať súbor dohody akciou 'Vytvoriť súbor dohody'")
        elif "stav_dohody" in self.cleaned_data and self.cleaned_data["stav_dohody"] == StavDohody.NAPODPIS:
            messages.warning(self.request, f"Podpísanú dohodu treba dať na sekretariát na odoslanie dohodárovi a následne stav dohody zmeniť na '{StavDohody.ODOSLANA_DOHODAROVI.label}'")
        elif "stav_dohody" in self.changed_data and self.cleaned_data["stav_dohody"] == StavDohody.DOKONCENA:
            #Vytvoriť záznam do denníka
            vec = f"Podpísaná dohoda {self.instance.cislo} od autora"
            cislo = nasledujuce_cislo(Dokument)
            dok = Dokument(
                cislo = cislo,
                cislopolozky = self.instance.cislo,
                datumvytvorenia = date.today(), 
                typdokumentu = TypDokumentu.DoVP if type(self.instance)== DoVP else TypDokumentu.DoPC if type(self.instance) == DoPC else TypDokumentu.DoBPS,
                inout = InOut.PRIJATY,
                adresat = self.instance.zmluvna_strana,
                vec = f'<a href="{self.instance.subor_dohody.url}">{vec}</a>',
                prijalodoslal=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
            )
            dok.save()
            messages.warning(self.request, f"Sken podpísanej dohody treba vložiť do poľa '{Dohoda.sken_dohody.label}'. Po vypršaní dohody treba spraviť záznam do 'Dohody - Vyplácanie dohôd'")

class DoPCForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        # do Admin treba pridať metódu get_form
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.initial['zdroj'] = 1       #111
        self.initial['program'] = 4     #nealokovaný
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

class DoVPForm(DohodaForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        # do Admin treba pridať metódu get_form
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.initial['zdroj'] = 1       #111
        self.initial['program'] = 4     #nealokovaný
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
        # do Admin treba pridať metódu get_form
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.initial['zdroj'] = 1       #111
        self.initial['program'] = 4     #nealokovaný
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
        self.initial['program'] = 4     #nealokovaný
        self.initial['zakazka'] = 2     #11010001 spol. zák.
        self.initial['ekoklas'] = 18    #611 - Tarifný plat, osobný plat, základný plat, funkčný plat, hodnostný plat, plat, vrátane ich náhrad
    class Meta:
        model = PlatovyVymer
        fields = "__all__"
        field_order = ["cislo_zamestnanca", "zamestnanec", "suborvymer", "datum_od", "datum_do", "tarifny_plat", "osobny_priplatok", "funkcny_priplatok", "platova_trieda", "platovy_stupen", "datum_postup", "zamestnanieroky", "zamestnaniedni", "popis_zmeny"]

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
                inout = InOut.ODOSLANY,
                typdokumentu = TypDokumentu.DoVP if type(dohoda)== DoVP else TypDokumentu.DoPC if type(dohoda) == DoPC else TypDokumentu.DoBPS,
                adresat = "Mzdové oddelenie", 
                vec = f'Podklady na vyplatenie dohody <a href="/admin/uctovnictvo/{dtype}/{dohoda.id}/change/">{dohoda}</a>',
                prijalodoslal=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                datumvytvorenia = date.today(), 
                cislopolozky = dohoda.cislo
            )
            dok.save()
            messages.warning(self.request, f"Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {cislo} '{vec}'")
            return self.cleaned_data
        except ValidationError as ex:
            raise ex
