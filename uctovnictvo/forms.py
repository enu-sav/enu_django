
from django.contrib import messages
from django import forms
from django.core.exceptions import ValidationError
from ipdb import set_trace as trace
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import nasledujuce_cislo, nasledujuce_VPD, nasledujuce_PPD, nasledujuce_Zmluva
from .models import PrijataFaktura, Objednavka, PrispevokNaStravne, DoPC, DoVP, DoBPS, PlatovyVymer
from .models import VyplacanieDohod, StavDohody, Dohoda, PravidelnaPlatba, TypPP, InternyPrevod, Nepritomnost, TypNepritomnosti
from .models import Najomnik, NajomnaZmluva, NajomneFaktura, TypPN, RozpoctovaPolozkaDotacia, RozpoctovaPolozkaPresun, RozpoctovaPolozka, Zmluva
from .models import PlatbaBezPrikazu, Pokladna, TypPokladna, SocialnyFond, PrispevokNaRekreaciu, OdmenaOprava
from .common import meno_priezvisko
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

#Umožní jednoducho definovať záznam v denníku
class DennikZaznam(forms.ModelForm):
    def dennik_zaznam(self, vec, typdokumentu, inout, adresat, url=None):
        cislo = nasledujuce_cislo(Dokument)
        dok = Dokument(
            cislo = cislo,
            cislopolozky = self.instance.cislo,
            #datumvytvorenia = self.cleaned_data['dane_na_uhradu'],
            datumvytvorenia = date.today(),
            typdokumentu = typdokumentu,
            inout = inout,
            adresat = adresat,
            vec = vec if not url else f'<a href="{url}">{vec}</a>',
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

class ObjednavkaForm(DennikZaznam):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        # do Admin treba pridať metódu get_form
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            nasledujuce = nasledujuce_cislo(Objednavka)
            self.fields[polecislo].help_text = f"Zadajte číslo novej objednávky v tvare {Objednavka.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísel existujúcich objednávok ako nasledujúce v poradí."
            self.initial[polecislo] = nasledujuce
    def clean(self):
        if 'datum_odoslania' in self.changed_data and not self.instance.subor_objednavky:
            raise ValidationError({"datum_odoslania": "Dátum odoslania možno vyplniť až po vygenerovaní objednávky."})
        if 'datum_odoslania' in self.changed_data:
            self.dennik_zaznam(f"Objednávka č. {self.instance.cislo}.", TypDokumentu.OBJEDNAVKA, InOut.ODOSLANY, self.instance.dodavatel, self.instance.subor_objednavky.url)

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
        polecislo = "nase_cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            self.fields[polecislo].help_text = "Zadajte číslo zmluvy (naše číslo alebo číslo dodávateľa). Na jednoduché rozlíšenie viacerých zmlúv toho istého dodávateľa možno v zátvorke uviesť krátku doplnkovú informáciu, napr. '2/2018 (dodávka plynu)'"
        polecislo = "nase_cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            self.fields[polecislo].help_text = "Zadajte číslo zmluvy (naše číslo alebo číslo dodávateľa). Na jednoduché rozlíšenie viacerých zmlúv toho istého dodávateľa možno v zátvorke uviesť krátku doplnkovú informáciu, napr. '2/2018 (dodávka plynu)'."
            nasledujuce = nasledujuce_Zmluva()
            self.fields[polecislo].help_text = f"Zadajte naše číslo novej zmluvy v tvare {Zmluva.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísel existujúcich zmlúv ako nasledujúce v poradí."
            self.initial[polecislo] = nasledujuce

class PrijataFakturaForm(DennikZaznam):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        # do Admin treba pridať metódu get_form
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        #trieda PrijataFaktura dedí od triedy Platba, tak tu nastavíme help text
        self.fields['zdroj'].help_text = f"Primárny zdroj platby a súvisiacej DPH"
        self.fields['zakazka'].help_text = f"Primárna zákazka platby a súvisiacej DPH"
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields:
            if not polecislo in self.initial:
                nasledujuce = nasledujuce_cislo(PrijataFaktura)
                self.fields[polecislo].help_text = f"Zadajte číslo novej faktúry v tvare {PrijataFaktura.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísiel existujúcich faktúr ako nasledujúce v poradí."
                self.initial[polecislo] = nasledujuce
            else: 
                self.fields[polecislo].help_text = f"Číslo faktúry v tvare {PrijataFaktura.oznacenie}-RRRR-NNN."
        self.fields['suma'].help_text = f"Vložte sumu s DPH.<br />Ak ide o <strong>platbu v cudzej mene</strong>, vyplňte polia 'Suma v cudzej mene' a 'Mena' a do tohoto poľa vložte nulu. Toto pole <strong>vyplňte až po určení</strong> skutočne vyplatenej sumy v EUR (podľa SOFTIPu).<br >Ak je <strong>faktúra v režime prenesenia daňovej povinnosti</strong>, zadajte <em>Áno</em> v poli <em>Prenos DP</em> a sem vložte sumu s DPH. Ak na takejto faktúre nie je uvedená suma s DPH, vloženú sumu treba <strong>vypočítať ručne</strong>."

    # Skontrolovať platnost a keď je všetko OK, spraviť záznam do denníka
    def clean(self):
        if 'cislo' in self.changed_data:
            if not self.cleaned_data['cislo'][:2] == PrijataFaktura.oznacenie:
                raise ValidationError({"cislo": "Nesprávne číslo. Zadajte číslo novej faktúry v tvare {PrijataFaktura.oznacenie}-RRRR-NNN"})
        #pole dane_na_uhradu možno vyplniť až po vygenerovani platobného príkazu akciou 
        #"Vytvoriť platobný príkaz a krycí list pre THS"
        if 'dane_na_uhradu' in self.changed_data:
            self.dennik_zaznam(f"Platobný príkaz na THS {self.instance.cislo} na vyplatenie", TypDokumentu.FAKTURA, InOut.ODOSLANY, "THS", self.instance.platobny_prikaz.url)
        return self.cleaned_data

class InternyPrevodForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        # do Admin treba pridať metódu get_form
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        #trieda InternyPrevod dedí od triedy Platba, tak tu nastavíme help text
        self.fields['zdroj'].help_text = f"Primárny zdroj platby a súvisiacej DPH"
        self.fields['zakazka'].help_text = f"Primárna zákazka platby a súvisiacej DPH"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        polecislo = "cislo"
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
            self.dennik_zaznam(f"Platobný príkaz na THS {self.instance.cislo} na vyplatenie", TypDokumentu.INTERNYPREVOD, InOut.ODOSLANY, "THS", self.instance.platobny_prikaz.url)
        return self.cleaned_data

class PravidelnaPlatbaForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        # do Admin treba pridať metódu get_form
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        polecislo = "cislo"
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
        if not 'zdroj' in self.initial: self.initial['zdroj'] = 1       #111
        if not 'program' in self.initial: self.initial['program'] = 4     #nealokovaný
        if not 'zakazka' in self.initial: self.initial['zakazka'] = 2     #11010001 spol. zák.	Činnosti z prostriedkov SAV - rozpočet 111
        if not 'ekoklas' in self.initial: self.initial['ekoklas'] = 108   #642014 Transfery jednotlivcom
        if not 'cinnost' in self.initial: self.initial['cinnost'] = 2     #1a
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
        if not 'zdroj' in self.initial: self.initial['zdroj'] = 1       #111
        if not 'program' in self.initial: self.initial['program'] = 4     #nealokovaný
        if not 'zakazka' in self.initial: self.initial['zakazka'] = 1     #Beliana
        if not 'ekoklas' in self.initial: self.initial['ekoklas'] = 58    #633018	Licencie

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
                    messages.warning(self.request, 
                        format_html(
                            'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>, treba v ňom doplniť údaje o prijatí.',
                            mark_safe(f'<a href="/admin/dennik/dokument/{dok.id}/change/">{cislo}</a>'),
                            vec
                            )
                    )
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
        elif "stav_dohody" in self.changed_data and self.cleaned_data["stav_dohody"] == StavDohody.PODPISANA_DOHODAROM:
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
            messages.warning(self.request, 
                format_html(
                    'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>, treba v ňom doplniť údaje o prijatí.',
                    mark_safe(f'<a href="/admin/dennik/dokument/{dok.id}/change/">{cislo}</a>'),
                    vec
                    )
            )
            messages.warning(self.request, f"Sken podpísanej dohody treba vložiť do poľa 'Skenovaná dohoda'. Po vypršaní platnosti dohody treba spraviť záznam do 'PaM - Vyplácanie dohôd'")

class DoPCForm(DohodaForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        # do Admin treba pridať metódu get_form
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if not 'zdroj' in self.initial: self.initial['zdroj'] = 1       #111
        if not 'program' in self.initial: self.initial['program'] = 4     #nealokovaný
        if not 'zakazka' in self.initial: self.initial['zakazka'] = 1     #Beliana
        if not 'ekoklas' in self.initial: self.initial['ekoklas'] = 97    #637027 - Odmeny zamestnancov mimopracovného pomeru
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
        if not 'zdroj' in self.initial: self.initial['zdroj'] = 1       #111
        if not 'program' in self.initial: self.initial['program'] = 4     #nealokovaný
        if not 'zakazka' in self.initial: self.initial['zakazka'] = 1     #Beliana
        if not 'ekoklas' in self.initial: self.initial['ekoklas'] = 97    #637027 - Odmeny zamestnancov mimopracovného pomeru
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
        if not 'zdroj' in self.initial: self.initial['zdroj'] = 1       #111
        if not 'program' in self.initial: self.initial['program'] = 4     #nealokovaný
        if not 'zakazka' in self.initial: self.initial['zakazka'] = 1     #Beliana
        if not 'ekoklas' in self.initial: self.initial['ekoklas'] = 97    #637027 - Odmeny zamestnancov mimopracovného pomeru
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
        if not 'zdroj' in self.initial: self.initial['zdroj'] = 1       #111
        if not 'cinnost' in self.initial: self.initial['cinnost'] = 2     #Hlavná činnosť 26/1a
        if not 'program' in self.initial: self.initial['program'] = 4     #nealokovaný
        if not 'zakazka' in self.initial: self.initial['zakazka'] = 2     #11010001 spol. zák.
        if not 'ekoklas' in self.initial: self.initial['ekoklas'] = 18    #611 - Tarifný plat, osobný plat, základný plat, funkčný plat, hodnostný plat, plat, vrátane ich náhrad
    class Meta:
        model = PlatovyVymer
        fields = "__all__"
        field_order = ["cislo_zamestnanca", "zamestnanec", "suborvymer", "datum_od", "datum_do", "tarifny_plat", "osobny_priplatok", "funkcny_priplatok", "platova_trieda", "platovy_stupen", "datum_postup", "zamestnanieroky", "zamestnaniedni", "popis_zmeny"]

class OdmenaOpravaForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if not 'zdroj' in self.initial: self.initial['zdroj'] = 1       #111
        if not 'program' in self.initial: self.initial['program'] = 4     #nealokovaný
        if not 'zakazka' in self.initial: self.initial['zakazka'] = 2     #11010001 spol. zák.
        if not 'ekoklas' in self.initial: self.initial['ekoklas'] = 18    #611 - Tarifný plat, osobný plat, základný plat, funkčný plat, hodnostný plat, plat, vrátane ich náhrad
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            nasledujuce = nasledujuce_cislo(OdmenaOprava)
            self.fields[polecislo].help_text = f"Zadajte číslo v tvare {OdmenaOprava.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísel existujúcich záznamov ako nasledujúce v poradí."
            self.initial[polecislo] = nasledujuce
    class Meta:
        model = OdmenaOprava
        fields = "__all__"

    # Skontrolovať platnost a keď je všetko OK, spraviť záznam do denníka
    def clean(self):
        try:
            if 'cislo' in self.changed_data:
                if not self.cleaned_data['cislo'][:3] == OdmenaOprava.oznacenie:
                    raise ValidationError({"cislo": "Nesprávne číslo. Zadajte číslo novej žiadosti v tvare {OdmenaOprava.oznacenie}-RRRR-NNN"})
            if "subor_odmeny" in self.changed_data:
                cislo = self.cleaned_data['cislo']
                messages.warning(self.request, f'Do záznamu {cislo} bol pridaný súbor so zoznamom odmien. Vygenerujte pre neho Platobný príkaz a krycí list (akcia "Vytvoriť krycí list"). Pritom sa vytvoria záznamy pre všetky odmeny zo súboru (pre tieto záznamy sa individuálne platobné príkazy negenerujú).')
        except ValidationError as ex:
            raise ex
        return self.cleaned_data

class PrispevokNaRekreaciuForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if not 'zdroj' in self.initial: self.initial['zdroj'] = 1       #111
        if not 'program' in self.initial: self.initial['program'] = 4     #nealokovaný
        if not 'zakazka' in self.initial: self.initial['zakazka'] = 2     #11010001 spol. zák.
        if not 'ekoklas' in self.initial: self.initial['ekoklas'] = 83    #637006 - náhrady
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            nasledujuce = nasledujuce_cislo(PrispevokNaRekreaciu)
            self.fields[polecislo].help_text = f"Zadajte číslo žiadosti o príspevok na rekreáciu v tvare {PrispevokNaRekreaciu.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísel existujúcich záznamov ako nasledujúce v poradí."
            self.initial[polecislo] = nasledujuce
    class Meta:
        model = PrispevokNaRekreaciu
        fields = "__all__"

    # Skontrolovať platnost a keď je všetko OK, spraviť záznam do denníka
    def clean(self):
        if 'cislo' in self.changed_data:
            if not self.cleaned_data['cislo'][:3] == PrispevokNaRekreaciu.oznacenie:
                raise ValidationError({"cislo": "Nesprávne číslo. Zadajte číslo novej žiadosti v tvare {PrispevokNaRekreaciu.oznacenie}-RRRR-NNN"})
        try:
            #pole dane_na_uhradu možno vyplniť až po vygenerovani platobného príkazu akciou 
            #"Vytvoriť platobný príkaz a krycí list pre THS"
            if 'subor_ziadost' in self.changed_data and 'datum' in self.changed_data and 'zamestnanec' in self.changed_data:
                vec = f"Príspevok na rekreáciu {self.cleaned_data['zamestnanec'].priezvisko} - žiadosť"
                cislo = nasledujuce_cislo(Dokument)
                dok = Dokument(
                    cislo = cislo,
                    datum = self.cleaned_data["datum"],
                    cislopolozky = self.cleaned_data['cislo'],
                    #datumvytvorenia = self.cleaned_data['dane_na_uhradu'],
                    datumvytvorenia = date.today(),
                    typdokumentu = TypDokumentu.REKREACIA,
                    inout = InOut.PRIJATY,
                    adresat = meno_priezvisko(self.cleaned_data['zamestnanec']),
                    vec = vec,
                    prijalodoslal=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                )
                dok.save()
                messages.warning(self.request, 
                    format_html(
                        'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>, treba v ňom doplniť údaje o prijatí žiadosti."',
                        mark_safe(f'<a href="/admin/dennik/dokument/{dok.id}/change/">{cislo}</a>'),
                        vec
                        )
                )
                messages.warning(self.request, 'Žiadosť treba dať na podpis vedeniu. Po podpísaní vyplňte pole "Dátum podpisu žiadosti"')
            elif 'datum_podpisu_ziadosti' in self.changed_data:
                vec = f"Príspevok na rekreáciu {self.instance.zamestnanec.priezvisko} - žiadosť"
                cislo = nasledujuce_cislo(Dokument)
                dok = Dokument(
                    cislo = cislo,
                    cislopolozky = self.instance.cislo,
                    #datumvytvorenia = self.cleaned_data['dane_na_uhradu'],
                    datumvytvorenia = date.today(),
                    typdokumentu = TypDokumentu.REKREACIA,
                    inout = InOut.ODOSLANY,
                    adresat = "PaM",
                    vec = f'<a href="{self.instance.subor_ziadost.url}">{vec}</a>',
                    prijalodoslal=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                )
                dok.save()
                messages.warning(self.request, 'Podpísanú žiadosť treba odoslať na PaM.')
                messages.warning(self.request, 
                    format_html(
                        'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>, treba v ňom doplniť údaje o odoslaní podpísanej žiadosti na PaM.',
                        mark_safe(f'<a href="/admin/dennik/dokument/{dok.id}/change/">{cislo}</a>'),
                        vec
                        )
                )
                messages.warning(self.request, 'PaM vytvorí a odošle vyúčtovanie príspevku. Po jeho prijatí vyplňte polia "Vyúčtovanie príspevku", "Na vyplatenie" a "Vyplatené v".')
            elif 'subor_vyuctovanie' in self.changed_data and 'prispevok' in self.changed_data and 'vyplatene_v_obdobi' in self.changed_data:
                if self.cleaned_data['prispevok'] < 0 and PrispevokNaRekreaciu.check_vyplatene_v(self.cleaned_data['vyplatene_v_obdobi']):
                    vec = f"Príspevok na rekreáciu {self.instance.zamestnanec.priezvisko} - vyúčtovanie"
                    cislo = nasledujuce_cislo(Dokument)
                    dok = Dokument(
                        cislo = cislo,
                        cislopolozky = self.instance.cislo,
                        #datumvytvorenia = self.cleaned_data['dane_na_uhradu'],
                        datumvytvorenia = date.today(),
                        typdokumentu = TypDokumentu.REKREACIA,
                        inout = InOut.PRIJATY,
                        adresat = "PaM",
                        vec = vec,
                        prijalodoslal=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                    )
                    dok.save()
                    messages.warning(self.request, 
                        format_html(
                            'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>, treba v ňom doplniť údaje o prijatí vyúčtovania žiadosti o príspevok na rekreáciu.',
                            mark_safe(f'<a href="/admin/dennik/dokument/{dok.id}/change/">{cislo}</a>'),
                            vec
                            )
                    )
                    messages.warning(self.request, f'Pomocou akcie "Vytvoriť krycí list" vytvorte krycí list a spolu s vyúčtovaním ho dajte na podpis. Po podpísaní ich dajte na sekretariát na odoslanie a vyplňte pole "Dátum odoslania KL".')
            elif 'datum_kl' in self.changed_data:
                vec = f"Príspevok na rekreáciu {self.instance.zamestnanec.priezvisko} - vyúčtovanie"
                cislo = nasledujuce_cislo(Dokument)
                dok = Dokument(
                    cislo = cislo,
                    cislopolozky = self.instance.cislo,
                    #datumvytvorenia = self.cleaned_data['dane_na_uhradu'],
                    datumvytvorenia = date.today(),
                    typdokumentu = TypDokumentu.REKREACIA,
                    inout = InOut.ODOSLANY,
                    adresat = "PaM",
                    vec = f'<a href="{self.instance.subor_vyuctovanie.url}">{vec}</a>',
                    prijalodoslal=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                )
                dok.save()
                messages.warning(self.request, 
                    format_html(
                        'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>, treba v ňom doplniť údaje o odoslaní vyúčtovania a krycieho list.',
                        mark_safe(f'<a href="/admin/dennik/dokument/{dok.id}/change/">{cislo}</a>'),
                        vec
                        )
                )
        except ValidationError as ex:
            raise ex
        return self.cleaned_data

class NepritomnostForm(DennikZaznam):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
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

    # Skontrolovať platnost a prípadne spraviť zmeny

    def clean(self): 
        if self.instance.subor_nepritomnost: #Sumárna neprítomnosť
            if 'datum_odoslania' in self.changed_data and not self.instance.subor_nepritomnost_exp:
                raise ValidationError({"datum_odoslania": "Dátum odoslania možno vyplniť až po vygenerovaní súboru s neprítomnosťou akciou 'Exportovať neprítomnosť pre učtáreň'."})
            if 'datum_odoslania' in self.changed_data:
                self.dennik_zaznam(f"Neprítomnosť č. {self.instance.cislo}.", TypDokumentu.NEPRITOMNOST, InOut.ODOSLANY, "THS", self.instance.subor_nepritomnost_exp.url)
        else: #Individuálna neprítomnosť:
            if self.cleaned_data["nepritomnost_typ"] in [TypNepritomnosti.LEKAR, TypNepritomnosti.LEKARDOPROVOD] and not self.cleaned_data["dlzka_nepritomnosti"]:
                zamestnanec = self.cleaned_data["zamestnanec"]
                #Doplniť denný úväzok zamestnanca v deň neprítomnosti
                qs = PlatovyVymer.objects.filter(zamestnanec=zamestnanec, datum_od__lte=self.cleaned_data['nepritomnost_od'], datum_do__gte=self.cleaned_data['nepritomnost_od'] )
                if not qs:  #Aktuálny výmer nie je ukončený
                    qs = PlatovyVymer.objects.filter(zamestnanec=zamestnanec, datum_od__lte=self.cleaned_data['nepritomnost_od'], datum_do__isnull=True)
                self.cleaned_data["dlzka_nepritomnosti"] = qs[0].uvazok_denne
                messages.warning(self.request, f"Dĺžka neprítomnosti nebola vyplnená. Doplnená bola doba {self.cleaned_data['dlzka_nepritomnosti']} hod., t.j. jeden pracovný deň zamestnanca.")
            elif not self.cleaned_data["nepritomnost_typ"] in [TypNepritomnosti.LEKAR, TypNepritomnosti.LEKARDOPROVOD] and self.cleaned_data["dlzka_nepritomnosti"]:
                self.cleaned_data["dlzka_nepritomnosti"] = None
                messages.warning(self.request, "Dĺžka neprítomnosti sa pre daný typ neprítomnosti neuvádza. Zadaná hodnota bola odstránená.")
            return self.cleaned_data

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
            messages.warning(self.request, 
                format_html(
                    'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>, treba v ňom doplniť údaje o prijatí.',
                    mark_safe(f'<a href="/admin/dennik/dokument/{dok.id}/change/">{cislo}</a>'),
                    vec
                    )
            )
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
            self.fields[polecislo].help_text = f"Zadajte číslo položky v tvare {RozpoctovaPolozkaPresun.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísel existujúcich položiek ako nasledujúce v poradí."
            self.initial[polecislo] = nasledujuce

class RozpoctovaPolozkaForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            nasledujuce = nasledujuce_cislo(RozpoctovaPolozka)
            self.fields[polecislo].help_text = f"Zadajte číslo položky v tvare {RozpoctovaPolozka}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísel existujúcich položiek ako nasledujúce v poradí.<br />Ak v poli 'Za rok' zadáte nasledujúci rok, po uložení sa číslo automaticky zmení na nasledujúce číslo budúceho roku."
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
            self.fields[polecislo].help_text = f"Zadajte číslo položky v tvare {RozpoctovaPolozkaDotacia.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce}' bolo určené na základe čísel existujúcich položiek ako nasledujúce v poradí.<br />Ak v poli 'Za rok' zadáte nasledujúci rok, po uložení sa číslo automaticky zmení na nasledujúce číslo budúceho roku."
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
        if not 'zdroj' in self.initial: self.initial['zdroj'] = 3       #42 - Iné vlastné zdroje 
        if not 'program' in self.initial: self.initial['program'] = 4     #nealokovaný
        if not 'zakazka' in self.initial: self.initial['zakazka'] = 8     #42002200 - Prenájom priestorov, zákl. služby, fotovoltaika,
        if not 'ekoklas' in self.initial: self.initial['ekoklas'] = 12    #223001 - Za predaj výrobkov, tovarov a služieb

    # Skontrolovať platnost a keď je všetko OK, spraviť záznam do denníka
    def clean(self):
        if 'cislo' in self.changed_data:
            if not self.cleaned_data['cislo'][:2] == NajomneFaktura.oznacenie:
                raise ValidationError({"cislo": "Nesprávne číslo. Zadajte číslo novej platby v tvare {NajomneFaktura.oznacenie}-RRRR-NNN"})
        #Ak vytvárame novú platbu, doplniť platby do konca roka
        #if 'typ' in self.changed_data:
            # skontrolovať znamienko
            #if self.cleaned_data['typ'] == TypPN.VYUCTOVANIE:   #ide o príjem
                #return self.cleaned_data

            #if  self.cleaned_data['suma'] < 0:  self.cleaned_data['suma'] *= -1

            #rok, poradie = re.findall(r"-([0-9]+)-([0-9]+)", self.cleaned_data['cislo'])[0]
            #rok = int(rok)
            #poradie = int(poradie) + 1
            #doplniť platby štvrťročne
            #začiatočný mesiac doplnených platieb
            #zmesiac = ((self.cleaned_data['splatnost_datum'].month-1)//3+1)*3 + 1
            #for mesiac in range(zmesiac, 13, 3):
                #vypĺňa sa: ['zdroj', 'zakazka', 'ekoklas', 'splatnost_datum', 'suma', 'objednavka_zmluva', 'typ']
                #dup = NajomneFaktura(
                    #zdroj = self.cleaned_data['zdroj'],
                    #zakazka = self.cleaned_data['zakazka'],
                    #program = self.cleaned_data['program'],
                    #ekoklas = self.cleaned_data['ekoklas'],
                    #suma = self.cleaned_data['suma'],
                    #typ = self.cleaned_data['typ'],
                    #cislo = "%s-%d-%03d"%(NajomneFaktura.oznacenie, rok, poradie),
                    #splatnost_datum = date(rok, mesiac, self.cleaned_data['splatnost_datum'].day),
                    #zmluva = self.cleaned_data['zmluva']
                    #)
                #poradie += 1
                #dup.save()

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

        nasledujuceVPD = nasledujuce_VPD()
        nasledujucePPD = nasledujuce_PPD()
        # nasledujúce číslo Výdavkového pokladničného dokladu
        self.fields["cislo_VPD"].help_text = f"Poradové číslo PD (pokladničného dokladu).<br />Ak necháte prázdne a nejde o dotáciu, <strong>doplní sa nasledujúce číslo PD</strong> (VPD: {nasledujuceVPD}, PPD: {nasledujucePPD}), ktoré bolo určené na základe čísiel existujúcich PD ako nasledujúce v poradí."

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
