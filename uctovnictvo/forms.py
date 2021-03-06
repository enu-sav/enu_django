
from django.contrib import messages
from django import forms
from django.core.exceptions import ValidationError
from ipdb import set_trace as trace
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import nasledujuce_cislo, nasledujuce_VPD
from .models import PrijataFaktura, Objednavka, PrispevokNaStravne, DoPC, DoVP, DoBPS, PlatovyVymer
from .models import VyplacanieDohod, StavDohody, Dohoda, PravidelnaPlatba, TypPP, InternyPrevod, Nepritomnost
from .models import Najomnik, NajomnaZmluva, NajomneFaktura, TypPN, RozpoctovaPolozkaDotacia, RozpoctovaPolozkaPresun
from .models import PlatbaBezPrikazu, Pokladna, TypPokladna, SocialnyFond
from dennik.models import Dokument, SposobDorucenia, TypDokumentu, InOut
from datetime import date, datetime
import re

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
            self.fields[polecislo].help_text = f"Zadajte číslo novej objednávky v tvare {Objednavka.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísel existujúcich objednávok ako nasledujúce v poradí."
            self.initial[polecislo] = nasledujuce

class PlatbaBezPrikazuForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            nasledujuce = nasledujuce_cislo(PlatbaBezPrikazu)
            self.fields[polecislo].help_text = f"Zadajte číslo novej objednávky v tvare {PlatbaBezPrikazu.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísel existujúcich objednávok ako nasledujúce v poradí."
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
                self.fields[polecislo].help_text = f"Zadajte číslo novej faktúry v tvare {PrijataFaktura.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísiel existujúcich faktúr ako nasledujúce v poradí."
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

class InternyPrevodForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        # do Admin treba pridať metódu get_form
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields:
            if not polecislo in self.initial:
                nasledujuce = nasledujuce_cislo(InternyPrevod)
                self.fields[polecislo].help_text = f"Zadajte číslo novej platby v tvare {InternyPrevod.oznacenie}-RRRR-NNN'. Predvolené číslo '{nasledujuce}' bolo určené na základe čísiel existujúcich platieb ako nasledujúce v poradí."
                self.initial[polecislo] = nasledujuce
            else:
                self.fields[polecislo].help_text = f"Číslo platby v tvare {InternyPrevod.oznacenie}-RRRR-NNN."
        if "splatnost_datum" in self.fields:
            if not "splatnost_datum" in self.initial:
                self.fields["splatnost_datum"].help_text = f"Zadajte dátum splatnosti prvého vyplácania (obvykle v januári). Po uložení sa vytvorí záznam pre všetky opakovania pravidelnej platby do konca roka."
            else:
                self.fields["splatnost_datum"].help_text = f"Dátum splatnosti"

    # Skontrolovať platnost a keď je všetko OK, spraviť záznam do denníka
    def clean(self):
        if 'cislo' in self.changed_data:
            if not self.cleaned_data['cislo'][:2] == InternyPrevod.oznacenie:
                raise ValidationError({"cislo": "Nesprávne číslo. Zadajte číslo novej platby v tvare {InternyPrevod.oznacenie}-RRRR-NNN"})
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
                dup = InternyPrevod(
                    zdroj = self.cleaned_data['zdroj'],
                    zakazka = self.cleaned_data['zakazka'],
                    program = self.cleaned_data['program'],
                    ekoklas = self.cleaned_data['ekoklas'],
                    suma = self.cleaned_data['suma'],
                    typ = self.cleaned_data['typ'],
                    cislo = "%s-%d-%03d"%(InternyPrevod.oznacenie, rok, poradie),
                    splatnost_datum = date(rok, mesiac, self.cleaned_data['splatnost_datum'].day)
                    )
                #nepovinné pole
                if 'objednavka_zmluva' in self.changed_data:
                    dup.objednavka_zmluva = self.cleaned_data['objednavka_zmluva']
                poradie += 1
                dup.save()
                pass

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
                typdokumentu = TypDokumentu.INTERNYPREVOD,
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
                self.fields[polecislo].help_text = f"Zadajte číslo novej platby v tvare {PravidelnaPlatba.oznacenie}-RRRR-NNN'. Predvolené číslo '{nasledujuce}' bolo určené na základe čísiel existujúcich platieb ako nasledujúce v poradí."
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
                #nepovinné pole
                if 'objednavka_zmluva' in self.changed_data:
                    dup.objednavka_zmluva = self.cleaned_data['objednavka_zmluva']
                poradie += 1
                dup.save()
                pass

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
                typdokumentu = TypDokumentu.PPLATBA,
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
        return self.cleaned_data

class PrispevokNaStravneForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['zdroj'] = 1       #111
        self.initial['program'] = 4     #nealokovaný
        self.initial['zakazka'] = 2     #11010001 spol. zák.	Činnosti z prostriedkov SAV - rozpočet 111
        self.initial['ekoklas'] = 108   #642014 Transfery jednotlivcom
        self.initial['cinnost'] = 2     #1a
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields:
            if not polecislo in self.initial:
                nasledujuce = nasledujuce_cislo(PrispevokNaStravne)
                self.fields[polecislo].help_text = f"Zadajte číslo novej platby v tvare {PrispevokNaStravne.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísiel existujúcich faktúr ako nasledujúce v poradí."
                self.initial[polecislo] = nasledujuce
            else:
                self.fields[polecislo].help_text = f"Číslo platby v tvare {PrispevokNaStravne.oznacenie}-RRRR-NNN."

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

class DoPCForm(DohodaForm):
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

class DoBPSForm(DohodaForm):
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
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            nasledujuce = nasledujuce_cislo(PlatovyVymer)
            self.fields[polecislo].help_text = f"Zadajte číslo platového výmeru v tvare {PlatovyVymer.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísel existujúcich vymerov ako nasledujúce v poradí."
            self.initial[polecislo] = nasledujuce
        self.initial['zdroj'] = 1       #111
        self.initial['program'] = 4     #nealokovaný
        self.initial['zakazka'] = 2     #11010001 spol. zák.
        self.initial['ekoklas'] = 18    #611 - Tarifný plat, osobný plat, základný plat, funkčný plat, hodnostný plat, plat, vrátane ich náhrad
    class Meta:
        model = PlatovyVymer
        fields = "__all__"
        field_order = ["cislo_zamestnanca", "zamestnanec", "suborvymer", "datum_od", "datum_do", "tarifny_plat", "osobny_priplatok", "funkcny_priplatok", "platova_trieda", "platovy_stupen", "datum_postup", "zamestnanieroky", "zamestnaniedni", "popis_zmeny"]

class NepritomnostForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            nasledujuce = nasledujuce_cislo(Nepritomnost)
            self.fields[polecislo].help_text = f"Zadajte číslo záznamu o neprítomnosti v tvare {Nepritomnost.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísel existujúcich záznamov ako nasledujúce v poradí."
            self.initial[polecislo] = nasledujuce
    class Meta:
        model = Nepritomnost
        fields = "__all__"

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

class NajomnaZmluvaForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            nasledujuce = nasledujuce_cislo(NajomnaZmluva)
            self.fields[polecislo].help_text = f"Zadajte číslo nájomnej zmluvy v tvare {NajomnaZmluva.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísel existujúcich zmlúv ako nasledujúce v poradí.<br />Ak ide o zmluvu podpísanú v minulosti, použite správny rok a poradové číslo."
            self.initial[polecislo] = nasledujuce


class RozpoctovaPolozkaPresunForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            nasledujuce = nasledujuce_cislo(RozpoctovaPolozkaPresun)
            self.fields[polecislo].help_text = f"Zadajte číslo položky v tvare {RozpoctovaPolozkaPresun.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísel existujúcich položky ako nasledujúce v poradí."
            self.initial[polecislo] = nasledujuce

class RozpoctovaPolozkaDotaciaForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            nasledujuce = nasledujuce_cislo(RozpoctovaPolozkaDotacia)
            self.fields[polecislo].help_text = f"Zadajte číslo položky v tvare {RozpoctovaPolozkaDotacia.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísel existujúcich položky ako nasledujúce v poradí."
            self.initial[polecislo] = nasledujuce

class NajomneFakturaForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            nasledujuce = nasledujuce_cislo(NajomneFaktura)
            self.fields[polecislo].help_text = f"Zadajte číslo platby v tvare {NajomneFaktura.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísel existujúcich platieb ako nasledujúce v poradí."
            self.initial[polecislo] = nasledujuce

    # Skontrolovať platnost a keď je všetko OK, spraviť záznam do denníka
    def clean(self):
        if 'cislo' in self.changed_data:
            if not self.cleaned_data['cislo'][:2] == NajomneFaktura.oznacenie:
                raise ValidationError({"cislo": "Nesprávne číslo. Zadajte číslo novej platby v tvare {NajomneFaktura.oznacenie}-RRRR-NNN"})
        #Ak vytvárame novú platbu, doplniť platby do konca roka
        if 'typ' in self.changed_data:
            # skontrolovať znamienko
            if self.cleaned_data['typ'] == TypPN.VYUCTOVANIE:   #ide o príjem
                return self.cleaned_data

            if  self.cleaned_data['suma'] < 0:  self.cleaned_data['suma'] *= -1

            rok, poradie = re.findall(r"-([0-9]+)-([0-9]+)", self.cleaned_data['cislo'])[0]
            rok = int(rok)
            poradie = int(poradie) + 1
            #doplniť platby štvrťročne
            #začiatočný mesiac doplnených platieb
            zmesiac = ((self.cleaned_data['splatnost_datum'].month-1)//3+1)*3 + 1
            for mesiac in range(zmesiac, 13, 3):
                #vyplňa sa: ['zdroj', 'zakazka', 'ekoklas', 'splatnost_datum', 'suma', 'objednavka_zmluva', 'typ']
                dup = NajomneFaktura(
                    zdroj = self.cleaned_data['zdroj'],
                    zakazka = self.cleaned_data['zakazka'],
                    program = self.cleaned_data['program'],
                    ekoklas = self.cleaned_data['ekoklas'],
                    suma = self.cleaned_data['suma'],
                    typ = self.cleaned_data['typ'],
                    cislo = "%s-%d-%03d"%(NajomneFaktura.oznacenie, rok, poradie),
                    splatnost_datum = date(rok, mesiac, self.cleaned_data['splatnost_datum'].day),
                    zmluva = self.cleaned_data['zmluva']
                    )
                poradie += 1
                dup.save()
                pass

        #pole dane_na_uhradu možno vyplniť až po vygenerovani platobného príkazu akciou 
        #"Vytvoriť platobný príkaz a krycí list pre THS"
        #Hack: Záznam sa vytvorí len vtedy, keď je nastavené self.instance.platobny_prikaz.url 
        # Umožní to zadať dátum dane_a_uhradu za prvé platby, ku ktorým se ešte nevytváral krycí list z Djanga 
        if 'dane_na_uhradu' in self.changed_data and self.instance.platobny_prikaz:
            vec = f"Platobný príkaz na THS {self.instance.cislo} na vyplatenie"
            cislo = nasledujuce_cislo(Dokument)
            dok = Dokument(
                cislo = cislo,
                cislopolozky = self.instance.cislo,
                #datumvytvorenia = self.cleaned_data['dane_na_uhradu'],
                datumvytvorenia = date.today(),
                typdokumentu = TypDokumentu.NAJOMNE,
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
        return self.cleaned_data

class PokladnaForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        #self.initial['zdroj'] = 1       #111
        #self.initial['program'] = 4     #nealokovaný
        #self.initial['zakazka'] = 2     #11010001 spol. zák.	Činnosti z prostriedkov SAV - rozpočet 111
        #self.initial['ekoklas'] = 108   #642014 Transfery jednotlivcom
        #self.initial['cinnost'] = 2     #1a
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields:
            if not polecislo in self.initial:
                nasledujuce = nasledujuce_cislo(Pokladna)
                self.fields[polecislo].help_text = f"Zadajte číslo nového záznamu pokladne v tvare {Pokladna.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísiel existujúcich záznamov ako nasledujúce v poradí."
                self.initial[polecislo] = nasledujuce
            else:
                self.fields[polecislo].help_text = f"Číslo záznamu pokladne v tvare {Pokladna.oznacenie}-RRRR-NNN."

        nasledujuce = nasledujuce_VPD()
        # nasledujúce číslo Výdavkového pokladničného dokladu
        self.fields["cislo_VPD"].help_text = f"Poradové číslo VPD (výdavkového pokladničného dokladu).<br />Ak necháte prázdne a nejde o dotáciu, <strong>doplní sa nasledujúce číslo '{nasledujuce}'</strong>, ktoré bolo určené na základe čísiel existujúcich VPD ako nasledujúce v poradí."

    # Skontrolovať platnost a prípadne spraviť zmeny
    def clean(self):
        if 'cislo' in self.changed_data:
            if not self.cleaned_data['cislo'][:2] == PrijataFaktura.oznacenie:
                raise ValidationError({"cislo": "Nesprávne číslo. Zadajte číslo novej faktúry v tvare {PrijataFaktura.oznacenie}-RRRR-NNN"})

        chyby={}
        if self.cleaned_data["typ_transakcie"] == TypPokladna.DOTACIA:
            nevyplna_sa = ["cislo_VPD", "zamestnanec", "zdroj", "zakazka", "ekoklas", "cinnost"]
            opravene = []
            for pole in nevyplna_sa:
                if pole in self.changed_data:
                    self.cleaned_data[pole] = None
                    opravene.append(self.fields[pole].label)
            if len(opravene) == 1:
                messages.warning(self.request, 
                    format_html(
                        'Vyplnené boli pole <em>{}</em>, to sa však v prípade dotácie nevypĺňa. Vyplnenie bolo zrušené',
                        ", ".join(opravene)
                        )
                    )
            elif len(opravene) > 1:
                messages.warning(self.request, 
                    format_html(
                        'Vyplnené boli polia <em>{}</em>, tie sa však v prípade dotácie nevypĺňajú. Vyplnenie bolo zrušené',
                        ", ".join(opravene)
                        )
                    )
        return self.cleaned_data

class SocialnyFondForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            nasledujuce = nasledujuce_cislo(SocialnyFond)
            self.fields[polecislo].help_text = f"Zadajte číslo novej položky v tvare {SocialnyFond.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísel existujúcich položiek ako nasledujúce v poradí."
            self.initial[polecislo] = nasledujuce
