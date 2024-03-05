
from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from ipdb import set_trace as trace
from .models import OsobaAutor, ZmluvaAutor, PlatbaAutorskaSumar, OsobaGrafik, ZmluvaGrafik, VytvarnaObjednavkaPlatba, StavZmluvy
from dennik.models import Dokument, SposobDorucenia, TypDokumentu, InOut
from dennik.forms import nasledujuce_cislo
from django.core.exceptions import ValidationError
from django.contrib import messages #import messages
import re
from datetime import date

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

class ZmluvaForm(forms.ModelForm):
    # Skontrolovať platnost a keď je všetko OK, spraviť záznam do denníka
    def clean(self):
        zo_name = ZmluvaAutor._meta.get_field('zmluva_odoslana').verbose_name
        zv_name = ZmluvaAutor._meta.get_field('zmluva_vratena').verbose_name
        vs_name = ZmluvaAutor._meta.get_field('vygenerovana_subor').verbose_name
        try:
            #kontrola
            #if not 'stav_zmluvy' in self.cleaned_data:
                #messages.warning(self.request, f"Akciou 'Vytvoriť súbory zmluvy' vytvorte súbory zmluvy")
                #return self.cleaned_data
            #elif 'honorar_ah' in self.changed_data:
            if 'honorar_ah' in self.changed_data:
                messages.warning(self.request, f"Akciou 'Vytvoriť súbory zmluvy' treba aktualizovať súbory zmluvy")
                return self.cleaned_data

            if 'zmluvna_strana' in self.changed_data:
                messages.warning(self.request, 
                    format_html(
                        'Teraz <strong>vytvorte súbory zmluvy</strong> akciou "Vytvoriť súbory zmluvy".'
                        )
                )
                return self.cleaned_data

            elif 'zmluva_odoslana' in self.changed_data:
                vec = f"Zmluva {self.instance.cislo} autorovi na podpis"
                cislo = nasledujuce_cislo(Dokument)
                dok = Dokument(
                    cislo = cislo,
                    cislopolozky = self.instance.cislo,
                    #datumvytvorenia = self.cleaned_data['zmluva_odoslana'],
                    datumvytvorenia = date.today(),
                    typdokumentu = TypDokumentu.AZMLUVA,
                    inout = InOut.ODOSLANY,
                    adresat = self.instance.zmluvna_strana,
                    vec = f'<a href="{self.instance.vygenerovana_subor.url}">{vec}</a>',
                    prijalodoslal=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                )
                dok.save()
                messages.warning(self.request,
                    format_html(
                        'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>.',
                        f"{cislo}",
                        vec
                        )
                    )
                self.cleaned_data['stav_zmluvy'] = StavZmluvy.ODOSLANA_AUTOROVI
                return self.cleaned_data
            elif 'zmluva_vratena' in self.changed_data:
                vec = f"Zmluva {self.instance.cislo} vrátená od autora"
                cislo = nasledujuce_cislo(Dokument)
                dok = Dokument(
                    cislo = cislo,
                    cislopolozky = self.instance.cislo,
                    #datumvytvorenia = self.cleaned_data['zmluva_vratena'],
                    datumvytvorenia = date.today(),
                    typdokumentu = TypDokumentu.AZMLUVA,
                    inout = InOut.PRIJATY,
                    adresat = self.instance.zmluvna_strana,
                    vec = f'<a href="{self.instance.vygenerovana_subor.url}">{vec}</a>',
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
                messages.warning(self.request, f"Zmluvu z poľa 'Vygenerovaný súbor zmluvy pre CRZ' treba dať príslušnej osobe na vloženie do CRZ.")
                messages.warning(self.request, f"Podpísanú zmluvu treba založiť do šanonu.")
                #url zmluvy
                if type(self.instance)==ZmluvaAutor:
                    url =f'<a href="/admin/zmluvy/osobaautor/{self.instance.zmluvna_strana.id}/change/">{self.instance.zmluvna_strana.priezvisko}{self.instance.zmluvna_strana.meno}</a>'
                    kto = "autora"
                else:
                    kto = "grafika"
                    url =f'<a href="/admin/zmluvy/osobagrafik/{self.instance.zmluvna_strana.id}/change/">{self.instance.zmluvna_strana.priezvisko}{self.instance.zmluvna_strana.meno}</a>'
                messages.warning(self.request, 
                    format_html(
                        "Ak bola podpísaná dohoda o nezdaňovaní treba vyplniť príslušné polia v zázname {}: {} .",
                        kto, mark_safe(url),
                        )
                    )
                self.cleaned_data['stav_zmluvy'] = StavZmluvy.VRATENA_OD_AUTORA
                return self.cleaned_data
            elif 'datum_zverejnenia_CRZ' in self.changed_data and 'url_zmluvy' in self.changed_data:
                vec = f"Zmluva {self.instance.cislo} vložená do CRZ."
                cislo = nasledujuce_cislo(Dokument)
                dok = Dokument(
                    cislo = cislo,
                    cislopolozky = self.instance.cislo,
                    datum = self.cleaned_data['datum_zverejnenia_CRZ'],
                    datumvytvorenia = date.today(), 
                    typdokumentu = TypDokumentu.AZMLUVA,
                    inout = InOut.ODOSLANY,
                    sposob = SposobDorucenia.WEB,
                    adresat = "CRZ",
                    vec = f'<a href="{self.instance.vygenerovana_subor.url}">{vec}</a>',
                    zaznamvytvoril=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                    prijalodoslal=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                )
                dok.save()
                self.cleaned_data['stav_zmluvy'] = StavZmluvy.ZVEREJNENA_V_CRZ
                messages.warning(self.request, 
                    format_html(
                        'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>',
                        mark_safe(f'<a href="/admin/dennik/dokument/{dok.id}/change/">{cislo}</a>'),
                        vec
                        )
                    )
                return self.cleaned_data
            #elif 'url_zmluvy' in self.changed_data or 'datum_zverejnenia_CRZ' in self.changed_data:
                #return self.cleaned_data
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
            'honorar_ah', 'url_zmluvy', 'datum_zverejnenia_CRZ', 'poznamka']

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
        # do Admin treba pridať metódu get_form
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        polecislo = "cislo"
        # Ak je pole readonly, tak sa nenachádza vo fields. Preto testujeme fields aj initial
        if polecislo in self.fields and not polecislo in self.initial:
            nasledujuce = nasledujuce_cislo(VytvarnaObjednavkaPlatba)
            self.fields[polecislo].help_text = f"Zadajte číslo novej objednávky v tvare {VytvarnaObjednavkaPlatba.oznacenie}-RRRR-NNN. Predvolené číslo '{nasledujuce} bolo určené na základe čísel existujúcich výtvarných objednávok ako nasledujúce v poradí."
            self.initial[polecislo] = nasledujuce

    # Skontrolovať platnost a keď je všetko OK, spraviť záznam do denníka
    def clean(self):
        if 'cislo' in self.changed_data:
            if not self.cleaned_data['cislo'][:2] == VytvarnaObjednavka.oznacenie:
                raise ValidationError({"cislo": "Nesprávne číslo. Zadajte číslo novej faktúry v tvare {VytvarnaObjednavka.oznacenie}-RRRR-NNN"})
        try:
            #pole dane_na_uhradu možno vyplniť až po vygenerovani platobného príkazu akciou 
            #"Vytvoriť platobný príkaz a krycí list"
            #trace()
            #Ak je už vygenerovaný príkaz ale zmenila sa výška honorára, treba upozorniť na potrebu opakovaného vytvorenia príkazu
            if "objednane_polozky" in self.changed_data:
                messages.warning(self.request, 
                    format_html(
                        'Teraz <strong>vytvorte súbor objednávky</strong> akciou "Vytvoriť súbor objednávky".'
                        )
               )
            if "honorar" in self.changed_data and not "poznamka" in self.changed_data: 
                raise ValidationError(f"Zmenili ste hodnotu v poli 'Honorár', ale nezadali ste dôvod v poli 'Poznámka'.")
            if "honorar" in self.changed_data and self.instance.subor_prikaz:
                messages.warning(self.request, 
                    format_html(
                        'Zmenili ste výšku honorára. Údaje v platobnom príkaze sú teraz neplatné.<br /><strong>Opakovane vytvorte súbor príkazu</strong>  akciou "Vytvoriť platobný príkaz a krycí list".'
                        )
               )
            if 'datum_objednavky' in self.changed_data:
                vec = f"Objednávka výtvarných diel {self.instance.cislo}"
                cislo = nasledujuce_cislo(Dokument)
                dok = Dokument(
                    cislo = cislo,
                    cislopolozky = self.instance.cislo,
                    #datumvytvorenia = self.cleaned_data['dane_na_uhradu'],
                    datumvytvorenia = date.today(),
                    typdokumentu = TypDokumentu.VOBJEDNAVKA,
                    inout = InOut.ODOSLANY,
                    adresat = self.instance.vytvarna_zmluva.zmluvna_strana,
                    sposob = SposobDorucenia.MAIL,
                    datum = date.today(),
                    vec = f'<a href="{self.instance.subor_objednavky.url}">{vec}</a>',
                    zaznamvytvoril=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                    prijalodoslal=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                )
                dok.save()
                messages.warning(self.request, 
                    format_html(
                        'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>, údaje o odoslaní (mailom) sú už vyplnené.<br/>Po dodaní objednaných položiek vytvorte príkaz na vyplatenie. Ak treba, upravte sumu honorára na vyplatenie.',
                        mark_safe(f'<a href="/admin/dennik/dokument/{dok.id}/change/">{cislo}</a>'),
                        vec
                        )
                )
            if 'dane_na_uhradu' in self.changed_data:
                vec = f"Platobný príkaz do učtárne {self.instance.cislo} na vyplatenie"
                cislo = nasledujuce_cislo(Dokument)
                dok = Dokument(
                    cislo = cislo,
                    cislopolozky = self.instance.cislo,
                    #datumvytvorenia = self.cleaned_data['dane_na_uhradu'],
                    datumvytvorenia = date.today(),
                    typdokumentu = TypDokumentu.VYPLACANIE_VH,
                    inout = InOut.ODOSLANY,
                    adresat = "THS",
                    vec = f'<a href="{self.instance.subor_prikaz.url}">{vec}</a>',
                    prijalodoslal=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                )
                dok.save()
                messages.warning(self.request, 
                    format_html(
                        'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>, sekretariát v ňom doplní údaje o odoslaní.',
                        mark_safe(f'<a href="/admin/dennik/dokument/{dok.id}/change/">{cislo}</a>'),
                        vec
                        )
                )
        except ValidationError as ex:
            raise ex
        return self.cleaned_data

class PlatbaAutorskaSumarForm(forms.ModelForm):
    #inicializácia polí
    def __init__(self, *args, **kwargs):
        # do Admin treba pridať metódu get_form
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    # Skontrolovať platnost a keď je všetko OK, spraviť záznam do denníka
    def clean(self):
        anv_name = PlatbaAutorskaSumar._meta.get_field('autori_na_vyplatenie').verbose_name
        du_name = PlatbaAutorskaSumar._meta.get_field('datum_uhradenia').verbose_name
        po_name = PlatbaAutorskaSumar._meta.get_field('podklady_odoslane').verbose_name
        klo_name = PlatbaAutorskaSumar._meta.get_field('kryci_list_odoslany').verbose_name
        vt_name = PlatbaAutorskaSumar._meta.get_field('vyplatit_ths').verbose_name
        v_name = PlatbaAutorskaSumar._meta.get_field('vyplatene').verbose_name
        zp_name = PlatbaAutorskaSumar.zrusit_platbu_name
        vpt_name = PlatbaAutorskaSumar.vytvorit_podklady_pre_THS_name
        zpd_name = PlatbaAutorskaSumar.zaznamenat_platby_do_db_name
        try:
            # ak je platba len vytvorená
            if 'cislo' in self.changed_data or not self.instance.vyplatit_ths:
                if 'cislo' in self.changed_data:
                    messages.warning(self.request, format_html(f"Ak ste tak ešte nespravili, z redakčných systémov exportujte csv súbory s údajmi pre vyplácanie a vložte ich do vytvoreného vyplácania."))
                messages.warning(self.request, format_html(f"Podklady na vyplatenie autorských honorárov vytvorte akciou <em>{vpt_name}</em>."))
            if 'podklady_odoslane' in self.changed_data:
                cislo = nasledujuce_cislo(Dokument)
                vec = f"Podklady na vyplatenie aut. honorárov za {self.instance.cislo}"
                if self.instance.vyplatit_ths:   # súbor existuje
                    dok = Dokument(
                        cislo = cislo,
                        #datum = self.cleaned_data['podklady_odoslane'],
                        cislopolozky = self.instance.cislo,
                        adresat = "Účtovník", 
                        inout = InOut.ODOSLANY,
                        typdokumentu = TypDokumentu.VYPLACANIE_AH,
                        datumvytvorenia = date.today(), 
                        vec = f'<a href="{self.instance.vyplatit_ths.url}">{vec}</a>, hárok ''Na vyplatenie''',
                        #zaznamvytvoril=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                        prijalodoslal=self.request.user.username,
                        #sposob = SposobDorucenia.MAIL
                    )
                    dok.save()
                    messages.warning(self.request, 
                        format_html(
                            'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>, treba v ňom doplniť údaje o odoslaní.',
                            mark_safe(f'<a href="/admin/dennik/dokument/{dok.id}/change/">{cislo}</a>'),
                            vec
                            )
                        )
                    messages.warning(self.request, format_html(f"Po odoslaní do učtárne týždeň čakajte na informáciu o neúspešných platbách.<br/>Potom v poli '{anv_name}' zmažte <em>nevyplatených autorov</em> (ak boli) a vyplňte pole '{du_name}'.") , messages.WARNING)
                    return self.cleaned_data
                else:
                    raise ValidationError(f"Pole '{po_name} možno vyplniť až po vygenerovaní súboru '{vt_name}'. ")
            if 'datum_uhradenia' in self.changed_data:
                    messages.warning(self.request, f"Teraz vytvorte finálny prehľad akciou '{zpd_name}'." , messages.WARNING)

            if 'datum_oznamenia' in self.changed_data:
                cislo = nasledujuce_cislo(Dokument)
                vec = f"Oznámenie nezdanených autorov na finančnú správu za {self.instance.cislo}"
                if self.instance.vyplatene:   # súbor existuje
                    dok = Dokument(
                        cislo = cislo,
                        cislopolozky = self.instance.cislo,
                        adresat = "Finanačná správa",
                        inout = InOut.ODOSLANY,
                        typdokumentu = TypDokumentu.VYPLACANIE_AH,
                        datumvytvorenia = date.today(), 
                        datum = self.cleaned_data['datum_oznamenia'],
                        vec = f'<a href="{self.instance.vyplatene.url}">{vec}</a>',
                        zaznamvytvoril=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                        prijalodoslal=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                        sposob = SposobDorucenia.WEB,
                    )
                else:
                    raise ValidationError(f"Pole '{name} možno vyplniť až po vygenerovaní súboru '{v_name}'. ")
                dok.save()
                messages.warning(self.request, 
                    format_html(
                        'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>',
                        mark_safe(f'<a href="/admin/dennik/dokument/{dok.id}/change/">{cislo}</a>'),
                        vec
                        )
                    )
                pass

            if 'datum_importovania' in self.changed_data:
                cislo = nasledujuce_cislo(Dokument)
                vec = f"Importovanie údajov o vyplatení do RS/WEBRS za {self.instance.cislo}"
                if self.instance.vyplatene:   # súbor existuje
                    dok = Dokument(
                        cislo = cislo,
                        cislopolozky = self.instance.cislo,
                        adresat = "RS/WEBRS",
                        inout = InOut.ODOSLANY,
                        typdokumentu = TypDokumentu.VYPLACANIE_AH,
                        datumvytvorenia = date.today(), 
                        datum = self.cleaned_data['datum_importovania'],
                        vec = f'<a href="{self.instance.vyplatene.url}">{vec}</a>"',
                        zaznamvytvoril=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                        prijalodoslal=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                        sposob = SposobDorucenia.WEB,
                    )
                else:
                    raise ValidationError(f"Pole '{name} možno vyplniť až po vygenerovaní súboru '{v_name}'. ")
                dok.save()
                messages.warning(self.request, 
                    format_html(
                        'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>',
                        mark_safe(f'<a href="/admin/dennik/dokument/{dok.id}/change/">{cislo}</a>'),
                        vec
                        )
                    )

            if 'kryci_list_odoslany' in self.changed_data:
                cislo = nasledujuce_cislo(Dokument)
                vec = f"Podklady na vyplatenie zrážkovej dane a odvodov do fondov za {self.instance.cislo}"
                if self.instance.vyplatene:   # súbor existuje
                    dok = Dokument(
                        cislo = cislo,
                        cislopolozky = self.instance.cislo,
                        adresat = "Účtovník", 
                        inout = InOut.ODOSLANY,
                        typdokumentu = TypDokumentu.VYPLACANIE_AH,
                        datumvytvorenia = date.today(), 
                        prijalodoslal=self.request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
                        vec = f'<a href="{self.instance.vyplatene.url}">{vec}</a>, hárok ''Krycí list''',
                    )
                else:
                    raise ValidationError(f"Pole '{name} možno vyplniť až po vygenerovaní súboru '{v_name}'. ")
                dok.save()
                messages.warning(self.request, 
                    format_html(
                        'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>, treba v ňom doplniť údaje o odoslaní.',
                        mark_safe(f'<a href="/admin/dennik/dokument/{dok.id}/change/">{cislo}</a>'),
                        vec
                        )
                    )
            return self.cleaned_data
        except ValidationError as ex:
            raise ex

    class Meta:
        model = PlatbaAutorskaSumar
        fields = "__all__"
