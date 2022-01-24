
from django import forms
from ipdb import set_trace as trace
from .models import Dokument, InOut, TypDokumentu
from zmluvy.models import ZmluvaAutor, ZmluvaGrafik, VytvarnaObjednavkaPlatba
from uctovnictvo.models import Objednavka, PrijataFaktura, PrispevokNaStravne, DoVP, DoPC, DoBPS
from datetime import datetime
from django.core.exceptions import ValidationError
import re

#Priradenie triedy k jej označeniu v čísle dokumentu
triedy = {
    ZmluvaAutor.oznacenie: ZmluvaAutor,
    ZmluvaGrafik.oznacenie: ZmluvaGrafik,
    VytvarnaObjednavkaPlatba.oznacenie: VytvarnaObjednavkaPlatba,
    Objednavka.oznacenie: Objednavka,
    PrijataFaktura.oznacenie: PrijataFaktura,
    PrispevokNaStravne.oznacenie: PrispevokNaStravne,
    DoPC.oznacenie: DoPC,
    DoVP.oznacenie: DoVP,
    DoBPS.oznacenie: DoBPS,
}

    #
def parse_cislo(cislo):
    return re.findall(r"([^- ]+)[ -]+([0-9]+)[ -]+([0-9]+)",cislo)

    #odstráni detegovateľné chyby
def normalizovat_cislo(cislo):
    typy = {
        ZmluvaAutor.oznacenie.lower(): ZmluvaAutor.oznacenie,
        ZmluvaGrafik.oznacenie.lower(): ZmluvaGrafik.oznacenie,
        VytvarnaObjednavkaPlatba.oznacenie.lower(): VytvarnaObjednavkaPlatba.oznacenie,
        Objednavka.oznacenie.lower(): Objednavka.oznacenie,
        PrijataFaktura.oznacenie.lower(): PrijataFaktura.oznacenie,
        PrispevokNaStravne.oznacenie.lower(): PrispevokNaStravne.oznacenie,
        DoPC.oznacenie.lower(): DoPC.oznacenie,
        DoVP.oznacenie.lower(): DoVP.oznacenie,
        DoBPS.oznacenie.lower(): DoBPS.oznacenie,
    }
    aux = parse_cislo(cislo)
    if aux:
        typ, rok, cislo = aux[0]
        if not typ.lower() in typy:
            raise ValidationError({"cislopolozky": f"Typ položky {typ} v databáze neexistuje. Overte správnosť zápisu."})
        return "%s-%s-%03d"%(typy[typ.lower()], rok, int(cislo))
    else:
        return cislo

#overí existenciu položky v databáze
def overit_polozku(cislo_polozky):
    aux = re.findall(r"([^-]+)-([0-9]+)-([0-9]+)",cislo_polozky)
    if aux:
        typ, rok, cislo = aux[0]
        polozka = triedy[typ].objects.filter(cislo = cislo_polozky)
        if not polozka:
            raise ValidationError({'cislopolozky':f"Položka {cislo_polozky} v databáze neexistuje. Overte jej správnosť."})
        return True #je podľa schémy X-RRRR-NNN
    return False    #nie je podľa schémy X-RRRR-NNN

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

class DokumentForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        # do Admin treba pridať metódu get_form
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields:
            if not polecislo in self.initial:
                nasledujuce = nasledujuce_cislo(Dokument)
                self.fields[polecislo].help_text = f"Zadajte číslo nového dokumentu v tvare {Dokument.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce} bolo určené na základe čísiel existujúcich dokumentov ako nasledujúce v poradí."
                self.initial[polecislo] = nasledujuce
            else:
                self.fields[polecislo].help_text = f"Číslo dokumentu v tvare {Dokument.oznacenie}-RRRR-NNN."

    # Ak ide o existujúci objekt, ako číslo očakávane X-RRRR-NNN
    def clean(self):
        # testovať správnosť čísla zadaného objektu
        if 'cislopolozky' in self.cleaned_data:
            cp = normalizovat_cislo(self.cleaned_data['cislopolozky'])
            self.cleaned_data['cislopolozky'] = cp
            podla_schemy = overit_polozku(cp) #skončí výnimkou, ak vyzerá byť ako podľa schémy X-RRRR-NNN, ale nie je
            if podla_schemy: #cislo je podľa schémy X-RRRR-NNN
                td_str = parse_cislo(cp)[0][0]
                if not self.cleaned_data['adresat']:
                    self.cleaned_data['adresat'] = triedy[td_str].objects.filter(cislo = cp)[0].adresat()
            else: #cislo nie je podľa schémy X-RRRR-NNN
                if not self.cleaned_data['adresat']:
                    raise ValidationError({'adresat':"Ak nie je zadaná položka databázy, tak pole 'Odosielateľ / Adresát' treba vyplniť"})
            if self.cleaned_data['inout'] == InOut.PRIJATY and not self.cleaned_data['naspracovanie']:
                raise ValidationError({'naspracovanie':"Ak ide o prijatý dokument, treba vyplniť pole 'Na spracovanie'"})
        return self.cleaned_data
