from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django import forms
from ipdb import set_trace as trace
from django.contrib import messages
from django.utils.translation import ngettext
from django.conf import settings
from django.contrib.auth import get_permission_codename
from django.db.models.functions import Collate
from simple_history.utils import update_change_reason
from django.db.models.fields.reverse_related import ManyToOneRel
import os, re
from datetime import datetime
from tempfile import TemporaryFile
import logging

# potrebné pre súčty, https://github.com/douwevandermeij/admin-totals
# upravená šablóna admin_totals/change_list_results_totals.html
from admin_totals.admin import ModelAdminTotals
from django.db.models import Sum

# Register your models here.
# pripajanie suborov k objektu: krok 1, importovať XxxSubor
from .models import OsobaAutor, ZmluvaAutor, PlatbaAutorskaOdmena, PlatbaAutorskaSumar, StavZmluvy, PlatbaAutorskaSumarSubor
from .models import AnoNie, SystemovySubor, PersonCommon, OsobaGrafik, ZmluvaGrafik, Zmluva, VytvarnaObjednavkaPlatba
from .common import VytvoritAutorskuZmluvu, VytvoritVytvarnuObjednavku
from .vyplatitautorske import VyplatitAutorskeOdmeny, VyplatitOdmenyGrafik
from dennik.forms import nasledujuce_cislo

from .forms import OsobaAutorForm, ZmluvaAutorForm, PlatbaAutorskaSumarForm, OsobaGrafikForm, ZmluvaGrafikForm, VytvarnaObjednavkaPlatbaForm

#https://pypi.org/project/django-admin-export-action/
from admin_export_action.admin import export_selected_objects

#umožniť zobrazenie autora v zozname zmlúv
#https://pypi.org/project/django-admin-relation-links/
from django_admin_relation_links import AdminChangeLinksMixin

#zobrazenie histórie
#https://django-simple-history.readthedocs.io/en/latest/admin.html
from simple_history.admin import SimpleHistoryAdmin

from import_export.admin import ImportExportModelAdmin

# Zoradiť položky v pulldown menu
def formfield_for_foreignkey(instance, db_field, request, **kwargs):
    if db_field.name == "zmluvna_strana":
        kwargs["queryset"] = OsobaAutor.objects.filter().order_by(Collate('rs_login', 'nocase'))
    return super(type(instance), instance).formfield_for_foreignkey(db_field, request, **kwargs)

class PersonCommonAdmin():
    def get_list_display(self, request):
        return ("datum_aktualizacie", "bankovy_kontakt", "adresa", "koresp_adresa")

    def adresa(self, obj):
        if obj.adresa_mesto:
            return f"{obj.adresa_ulica} {obj.adresa_mesto}, {obj.adresa_stat}".strip()
    adresa.short_description = "Trvalé bydlisko"

    def koresp_adresa(self, obj):
        if obj.koresp_adresa_mesto:
            return f"{obj.koresp_adresa_institucia} {obj.koresp_adresa_ulica} {obj.koresp_adresa_mesto}, {obj.koresp_adresa_stat}".strip()
    koresp_adresa.short_description = "Korešp. adresa"

class FyzickaOsobaAdmin(PersonCommonAdmin):
    def get_list_display(self, request):
        return ("menopriezvisko",'email', 'rezident', 'nevyplacat', 'zdanit', "dohodasubor", "datum_dohoda_oznamenie", "datum_dohoda_podpis") + super(FyzickaOsobaAdmin, self).get_list_display(request)

    def get_search_fields(self, request):
        return ("priezvisko", "email")

    def menopriezvisko(self, obj):
        if obj.priezvisko:
            mp = f"{obj.titul_pred_menom} {obj.meno} {obj.priezvisko}, {obj.titul_za_menom}".strip()
            mp = mp.replace(", None", "").replace("None ","")
            return mp
    menopriezvisko.short_description = "Meno a tituly"

class OsobaAuGaKoAdmin(FyzickaOsobaAdmin):
    def get_list_display(self, request):
        return ("odbor",) + super(OsobaAuGaKoAdmin, self).get_list_display(request)

    def get_search_fields(self, request):
        return ("odbor",) + super(OsobaAuGaKoAdmin, self).get_search_fields(request)

@admin.register(OsobaAutor)
#class OsobaAutorAdmin(AdminChangeLinksMixin, admin.ModelAdmin):
class OsobaAutorAdmin(OsobaAuGaKoAdmin, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    def get_list_display(self, request):
        return ("rs_login", 'zmluvy_link', 'platby_link') + super(OsobaAutorAdmin, self).get_list_display(request)

    def get_search_fields(self, request):
        return ("rs_login",) + super(OsobaAutorAdmin, self).get_search_fields(request)

    # modifikovať formulár na pridanie poľa Popis zmeny
    form = OsobaAutorForm
    #Ak pouzijeme 'fields', tak vznikne chyba suvisiaca so 'zmluvy_link' a 'platby_link'
    _fields = (
            'rs_login',
            'titul_pred_menom',
            'meno',
            'priezvisko',
            'titul_za_menom',
            'rodne_cislo',
            'bankovy_kontakt',
            'zdanit',
            'zdanit',
            'email',
            'rezident',
            'adresa_ulica',
            'adresa_mesto',
            'adresa_stat',
            'koresp_adresa_institucia',
            'koresp_adresa_ulica',
            'koresp_adresa_mesto',
            'koresp_adresa_stat',
            'odbor',
            'preplatok',
            'poznamka'
            )
    ordering = ('-datum_aktualizacie',)

    #Konfigurácia poľa zmluvy_link (pripojené k ZmluvaAutor cez ForeignKey)
    #changelist_links = ['zmluvy'];
    changelist_links = [
        ('zmluvy', {
            'label': 'Zmluvy',  # Used as label for the link
        }),
        ('platby', {
            'label': 'Platby',  # Used as label for the link
        })
    ]

    # zobraziť zoznam zmenených polí
    history_list_display = ['changed_fields']
    def changed_fields(self, obj):
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            return ", ".join(delta.changed_fields)
        return None

    #obj is None during the object creation, but set to the object being edited during an edit
    def get_readonly_fields(self, request, obj=None):
        if obj:
            if obj.zdanit == AnoNie.ANO:
                #ak su polia dohoda readonly, tak nemozeme zmenit stav zdanit==ANO nas zdanit==Nie
                #return ["rs_uid", "rs_login","datum_dohoda_podpis", "datum_dohoda_oznamenie", "dohodasubor"]
                return ["rs_uid", "rs_login"]
            else:
                return ["rs_uid", "rs_login"]
        else:
            return []

@admin.register(OsobaGrafik)
class OsobaGrafikAdmin(FyzickaOsobaAdmin, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    def get_list_display(self, request):
        #return ("priezvisko", 'zmluvy_link', 'platby_link') + super(OsobaGrafikAdmin, self).get_list_display(request)
        return ("priezvisko",) + super(OsobaGrafikAdmin, self).get_list_display(request)

    def get_search_fields(self, request):
        return ("priezvisko",) + super(OsobaGrafikAdmin, self).get_search_fields(request)

    # modifikovať formulár na pridanie poľa Popis zmeny
    form = OsobaGrafikForm
    ordering = ('-datum_aktualizacie',)

    #Konfigurácia poľa zmluvy_link (pripojené k ZmluvaGrafik cez ForeignKey)
    #changelist_links = ['zmluvy'];
    _changelist_links = [
        ('zmluvy', {
            'label': 'Zmluvy',  # Used as label for the link
        }),
        ('platby', {
            'label': 'Platby',  # Used as label for the link
        })
    ]

    # zobraziť zoznam zmenených polí
    history_list_display = ['changed_fields']
    def changed_fields(self, obj):
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            return ", ".join(delta.changed_fields)
        return None

class ZmluvaAdmin():
    #stránkovanie a 'Zobraziť všetko'
    list_max_show_all = 10000
    list_per_page = 50
    def get_list_display(self, request):
        return ('zmluvna_strana_link', 'stav_zmluvy', 'subor_zmluvy_html', 'subor_zmluvy_crz_html', 'zmluva_odoslana', 'zmluva_vratena',
            'url_zmluvy_html', 'crz_datum', 'datum_pridania', 'datum_aktualizacie')

    def get_search_fields(self, request):
        return ("cislo", "stav_zmluvy")

    #obj is None during the object creation, but set to the object being edited during an edit
    def get_readonly_fields(self, request, obj=None):
        fields = [f.name for f in Zmluva._meta.get_fields()]
        is_superuser=request.user.is_superuser
        if obj:
            if obj.stav_zmluvy and is_superuser:
                fields.remove("stav_zmluvy")
                fields.remove("poznamka")
            if obj.stav_zmluvy == StavZmluvy.VYTVORENA:
                fields.remove("zmluva_odoslana")
            elif obj.stav_zmluvy == StavZmluvy.ODOSLANA_AUTOROVI:
                fields.remove("zmluva_vratena")
            elif obj.stav_zmluvy == StavZmluvy.VRATENA_OD_AUTORA:
                if "url_zmluvy" in fields:
                    fields.remove("url_zmluvy")
                if "datum_zverejnenia_CRZ" in fields:
                    fields.remove("datum_zverejnenia_CRZ")
                if "podpisana_subor" in fields:
                    fields.remove("podpisana_subor")
            elif obj.stav_zmluvy == StavZmluvy.ZVEREJNENA_V_CRZ:
                if "url_zmluvy" in fields:
                    fields.remove("url_zmluvy")
            else:
                pass
                #fields.remove("zmluvna_strana")
                #fields.remove("honorar_ah")
            pass
        else:
            # V novej zmluve povoliť (teda pouzit remove) len: 
            fields.remove("cislo")
        pass
        return fields

    # formátovať pole url_zmluvy
    def url_zmluvy_html(self, obj):
        if obj:
            return format_html(f'<a href="{obj.url_zmluvy}" target="_blank">pdf</a>') if obj.url_zmluvy else None
        else:
            return None
    url_zmluvy_html.short_description = "Zmluva v CRZ"

    # formátovať pole súboru zmluvy
    def subor_zmluvy_html(self, obj):
        if obj:
            return format_html(f'<a href="{obj.vygenerovana_subor.url}" target="_blank">{obj.vygenerovana_subor.name.split("/")[-1]}</a>') if obj.vygenerovana_subor else None
        else:
            return None
    subor_zmluvy_html.short_description = "Súbor zmluvy"

    # formátovať pole súboru zmluvy
    def subor_zmluvy_crz_html(self, obj):
        if obj:
            return format_html(f'<a href="{obj.vygenerovana_crz_subor.url}" target="_blank">{obj.vygenerovana_crz_subor.name.split("/")[-1]}</a>') if obj.vygenerovana_crz_subor else None
        else:
            return None
    subor_zmluvy_crz_html.short_description = "Súbor pre CRZ"

    # formatovat datum
    def crz_datum(self, obj):
        return obj.datum_zverejnenia_CRZ.strftime("%d-%m-%Y") if obj and obj.datum_zverejnenia_CRZ else None
    crz_datum.short_description = "Platná od"

    # zobraziť zoznam zmenených polí
    history_list_display = ['changed_fields']
    def changed_fields(self, obj):
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            return ", ".join(delta.changed_fields)
        return None

    def vytvorit_subory_zmluvy(self, request, queryset):
        for zmluva  in queryset:
            if not zmluva.stav_zmluvy or zmluva.stav_zmluvy in ( StavZmluvy.VYTVORENA):  
                #vytvorene_subory: s cestou vzhľadom na MEDIA_ROOT 'AutorskeZmluvy/AdamAnton-1298/AdamAnton-1298.fodt'
                status, msg, vytvorene_subory = self.VytvoritZmluvu(zmluva)
                if status != messages.ERROR:
                    zmluva.stav_zmluvy = StavZmluvy.VYTVORENA
                    zmluva.datum_aktualizacie = timezone.now(),
                    for subor in vytvorene_subory:
                        if "CRZ" in subor:
                            zmluva.vygenerovana_crz_subor=subor
                        else:
                            zmluva.vygenerovana_subor=subor
                    zmluva.save()
                self.message_user(request, msg, status)
                self.message_user(request, f"Vytvorenú zmluvu dajte ju na podpis vedeniu Enú.\n Podpísanú zmluvu dajte na sekretariát na odoslanie autorovi a vyplňte pole 'Autorovi na podpis'", messages.WARNING)
            else:
                self.message_user(request, f"Súbory zmluvy {zmluva.cislo} neboli vytvorené, lebo zmluva je už v stave '{StavZmluvy(zmluva.stav_zmluvy).label}'", messages.ERROR)
                continue
    vytvorit_subory_zmluvy.short_description = f"Vytvoriť súbory zmluvy"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_subory_zmluvy.allowed_permissions = ('change',)
    actions = ['vytvorit_subory_zmluvy', export_selected_objects]

@admin.register(ZmluvaAutor)
class ZmluvaAutorAdmin(ZmluvaAdmin, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    # modifikovať formulár na pridanie poľa Popis zmeny
    form = ZmluvaAutorForm
    def get_list_display(self, request):
        return ("cislo", "honorar_ah") + super(ZmluvaAutorAdmin, self).get_list_display(request)

    #fields = ('cislo', 'stav_zmluvy', 'zmluva_odoslana', 'zmluva_vratena', 'zmluvna_strana',
            #'honorar_ah', 'url_zmluvy', 'datum_zverejnenia_CRZ', 'datum_pridania', 'datum_aktualizacie')
    ordering = ('-datum_aktualizacie',)
    def get_search_fields(self, request):
        return ("zmluvna_strana__rs_login", "honorar_ah") + super(ZmluvaAutorAdmin, self).get_search_fields(request)


    # zmluvna_strana_link: pridá autora zmluvy do zoznamu, vďaka AdminChangeLinksMixin
    # použité v ZmluvaAdmin
    change_links = ['zmluvna_strana']
    change_links = [
        ('zmluvna_strana', {
            'admin_order_field': 'zmluvna_strana__rs_login',  # Allow to sort members by `zmluvna_strana_link` column
        })
    ]

    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

    #obj is None during the object creation, but set to the object being edited during an edit
    def get_readonly_fields(self, request, obj=None):
        # polia rodičovskej triedy
        fields = super(ZmluvaAutorAdmin, self).get_readonly_fields(request, obj)
        #pridať nové polia aktuálnej triedy
        fields_cur = {f.name for f in ZmluvaAutor._meta.get_fields()}   #všetky polia akt. triedy
        fields_par = {f.name for f in Zmluva._meta.get_fields()}        #všetky polia rodičovskej triedy
        for f in fields_cur - fields_par:   #pridať rozdiel po jednom
            fields += (f,)
        if obj:
            if not obj.stav_zmluvy or obj.stav_zmluvy in [StavZmluvy.VYTVORENA]:
                fields.remove("honorar_ah")
        else:
            # V novej zmluve povoliť (teda pouzit remove) len: 
            fields.remove("honorar_ah")
            fields.remove("zmluvna_strana")
        return fields

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(ZmluvaAutorAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

    def VytvoritZmluvu(self, zmluva):
        return VytvoritAutorskuZmluvu(zmluva, "Šablóna autorskej zmluvy")  #Presne takto musí byť šablóna označená

@admin.register(ZmluvaGrafik)
class ZmluvaGrafikAdmin(ZmluvaAdmin, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    # modifikovať formulár na pridanie poľa Popis zmeny
    form = ZmluvaGrafikForm
    def get_list_display(self, request):
        return ("cislo", "zmluvna_strana_link") + super(ZmluvaGrafikAdmin, self).get_list_display(request)

    #fields = ('cislo', 'stav_zmluvy', 'zmluva_odoslana', 'zmluva_vratena', 'zmluvna_strana',
            #'honorar_ah', 'url_zmluvy', 'datum_zverejnenia_CRZ', 'datum_pridania', 'datum_aktualizacie')
    ordering = ('-datum_aktualizacie',)
    def get_search_fields(self, request):
        return ("zmluvna_strana__priezvisko",) + super(ZmluvaGrafikAdmin, self).get_search_fields(request)


    # zmluvna_strana_link: pridá autora zmluvy do zoznamu, vďaka AdminChangeLinksMixin
    # použité v ZmluvaAdmin
    change_links = [
        ('zmluvna_strana', {
            'admin_order_field': 'zmluvna_strana__priezvisko',  # Allow to sort members by `zmluvna_strana_link` column
        })
    ]

    #obj is None during the object creation, but set to the object being edited during an edit
    def get_readonly_fields(self, request, obj=None):
        fields = super(ZmluvaGrafikAdmin, self).get_readonly_fields(request, obj)
        #pridať nové polia aktuálnej triedy
        #ak sa nevylúči pole typu ManyToOneRel, nastane výnimka
        #Exception Value: __call__() missing 1 required keyword-only argument: 'manager'
        #Pole existuje preto, lebo ZmluvaGrafik vystupuje ako ForeignKey vo VytvarnaObjednavkaPlatba
        fields_cur = {f.name for f in ZmluvaGrafik._meta.get_fields() if type(f) != ManyToOneRel}  #všetky polia akt. triedy
        fields_par = {f.name for f in Zmluva._meta.get_fields()}        #všetky polia rodičovskej triedy
        for f in fields_cur - fields_par:   #pridať rozdiel po jednom
            fields += (f,)
        if obj:
            if obj.vygenerovana_subor: 
                pass
            else:
                fields.remove("zmluvna_strana")
                #fields.remove("podklady_odoslane")
            pass
        else:
            fields.remove("zmluvna_strana")
        return fields

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(ZmluvaGrafikAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

    def VytvoritZmluvu(self, zmluva):
        return VytvoritAutorskuZmluvu(zmluva, "Šablóna výtvarnej zmluvy")  #Presne takto musí byť šablóna označená

class PlatbaAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    # autor_link: pridá autora zmluvy do zoznamu, vďaka AdminChangeLinksMixin
    def get_list_display(self, request):
        return ('datum_uhradenia', 'honorar', 'odvod_LF', 'odvedena_dan', 'uhradena_suma')
    list_totals = [
            ('honorar', Sum),
            ('odvod_LF', Sum),
            ('odvedena_dan', Sum),
            ('uhradena_suma', Sum),
            ]

    # formatovat datum
    def datum_uhradenia(self, obj):
        return obj.datum_uhradenia.strftime("%d-%m-%Y")

@admin.register(PlatbaAutorskaOdmena)
class PlatbaAutorskaOdmenaAdmin(PlatbaAdmin):
    # autor_link: pridá autora zmluvy do zoznamu, vďaka AdminChangeLinksMixin
    def get_list_display(self, request):
        return ('platba', 'zmluva', 'autor_link', 'zdanit', 'rezident', 'podpis', 'oznamenie','cislo') + super(PlatbaAutorskaOdmenaAdmin, self).get_list_display(request)
    #stránkovanie a 'Zobraziť všetko'
    list_max_show_all = 10000
    list_per_page = 50

    def zdanit(self, obj):
        return f"{obj.autor.zdanit if obj.autor.zdanit else '-'}"
    zdanit.short_description = 'Zdanit'
    zdanit.admin_order_field = 'autor__zdanit'

    def podpis(self, obj):
        return f"{obj.autor.datum_dohoda_podpis if obj.autor.datum_dohoda_podpis else '-'}"
    podpis.short_description = 'Dátum podpisu'
    podpis.admin_order_field = 'autor__datum_dohoda_podpis'

    def oznamenie(self, obj):
        return f"{obj.autor.datum_dohoda_oznamenie if obj.autor.datum_dohoda_oznamenie else '-'}"
    oznamenie.short_description = 'Dátum oznámenia'
    oznamenie.admin_order_field = 'autor__datum_dohoda_oznamenie'

    def rezident(self, obj):
        return f"{obj.autor.rezident if obj.autor.rezident else '-'}"
    rezident.short_description = 'Rezident'
    rezident.admin_order_field = 'autor__rezident'

    def platba(self, obj):
        return f"{obj.autor.rs_login}-{obj.cislo}"
    platba.short_description = 'Platba'
    platba.admin_order_field = 'autor__rs_login'

    search_fields = ['cislo', "zmluva", "autor__rs_login"]
    actions = [export_selected_objects,]

    # zoraďovateľný odkaz na číslo zmluvy
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('autor', {
            'admin_order_field': 'autor__rs_login', # Allow to sort members by the `autor_link` column
        }),
        ('zdanit', {
            'admin_order_field': 'autor__zdanit',
        }),
    ]

    #Všetky polia sa generujú, takže nič nemožno editovať
    def get_readonly_fields(self, request, obj=None):
        #return ['zmluva', 'datum_uhradenia', 'preplatok_pred', 'honorar', 'odvod_LF', 'odvedena_dan', 'uhradena_suma']
        return {f.name for f in PlatbaAutorskaOdmena._meta.get_fields()}  #všetky polia akt. triedy

@admin.register(VytvarnaObjednavkaPlatba)
class VytvarnaObjednavkaPlatbaAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = VytvarnaObjednavkaPlatbaForm
    # autor_link: pridá autora zmluvy do zoznamu, vďaka AdminChangeLinksMixin
    list_display = ["cislo", "vytvarna_zmluva_link", "datum_dodania", "subor_objednavky", "honorar", "datum_objednavky", "subor_prikaz", "dane_na_uhradu", "datum_uhradenia", "datum_oznamenia", "_vyplatene", "odvedena_dan"]

    #search_fields = ['cislo', "zmluva", "autor__rs_login"]

    # zoraďovateľný odkaz na číslo zmluvy
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('vytvarna_zmluva', {
            'admin_order_field': 'vytvarna_zmluva', # Allow to sort members by the `autor_link` column
        }),
    ]

    actions = ['vytvorit_objednavku', "vytvorit_platobny_prikaz"]

    def _vyplatene(self, obj):
        if not obj.honorar or obj.odvedena_dan == None: return "-"
        return obj.honorar - obj.odvedena_dan - obj.odvod_LF
    _vyplatene.short_description = "Vyplatené"

    def get_readonly_fields(self, request, obj=None):
        readonly = ["cislo", "vytvarna_zmluva", "objednane_polozky", "datum_objednavky", "subor_objednavky", "honorar", "subor_prikaz", "dane_na_uhradu", "datum_uhradenia", "datum_oznamenia", "odvod_LF", "odvedena_dan", "poznamka"]
        editable = []
        if not obj:                                                 #nová položka
            editable = ["cislo", "vytvarna_zmluva", "objednane_polozky", "poznamka"]
        elif not obj.datum_objednavky and not obj.subor_objednavky: #ešte nevygenerovaný súbor objednávky
            editable = ["cislo", "vytvarna_zmluva", "objednane_polozky", "poznamka"]
        elif not obj.datum_objednavky and obj.subor_objednavky:     #vygenerovaný súbor objednávky
            editable = ["cislo", "vytvarna_zmluva", "objednane_polozky", "datum_objednavky", "poznamka"]
        elif obj.datum_objednavky and not obj.subor_prikaz:         #ešte nevygenerovaný príkaz
            editable = ["honorar", "poznamka"]
        elif not obj.dane_na_uhradu and obj.subor_prikaz:           #vygenerovaný príkaz
            editable = ["honorar", "dane_na_uhradu", "poznamka"]
        elif obj.dane_na_uhradu and obj.subor_prikaz:               #odoslané na THS, čakáme na dátum vyplatenia
            editable = ["datum_uhradenia", "datum_oznamenia", "poznamka"]
        for ed in editable: readonly.remove(ed)
        return readonly 

    def vytvorit_objednavku(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu objednávku", messages.ERROR)
            return
        objednavka = queryset[0]
        #vytvorene_subory: s cestou vzhľadom na MEDIA_ROOT 'AutorskeZmluvy/AdamAnton-1298/AdamAnton-1298.fodt'
        status, msg, subor = VytvoritVytvarnuObjednavku(objednavka, request.user)
        if status != messages.ERROR:
            objednavka.datum_aktualizacie = timezone.now(),
            objednavka.subor_objednavky=subor
            objednavka.save()
            self.message_user(request, msg, status)
            self.message_user(request, f"Vytvorenú objednávku odošlite autorovi mailom a následne vyplňte pole 'Dátum objednávky'.", messages.WARNING)
        else:
            self.message_user(request, f"Súbor objednávky {objednavka.cislo} nebol vytvorený: {msg}'", messages.ERROR)
    vytvorit_objednavku.short_description = f"Vytvoriť súbor objednávky"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_objednavku.allowed_permissions = ('change',)

    def vytvorit_platobny_prikaz(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu položku", messages.ERROR)
            return
        platba = queryset[0]
        if not platba.datum_objednavky:
            self.message_user(request, f"Platobný príkaz nemožno vytvoriť, lebo objednávka ešte nebola odoslaná.", messages.ERROR)
            return
        platba.odvod_LF = platba.honorar*settings.LITFOND_ODVOD/100
        platba.odvedena_dan = (platba.honorar- platba.odvod_LF)*settings.DAN_Z_PRIJMU/100 if platba.vytvarna_zmluva.zmluvna_strana.zdanit == AnoNie.ANO else 0
        prikaz = VyplatitOdmenyGrafik(platba)
        status, msg, vytvoreny_subor = prikaz.vytvorit_prikaz()
        if status != messages.ERROR:
            platba.subor_prikaz = vytvoreny_subor
            platba.save()
        self.message_user(request, msg, status)

    vytvorit_platobny_prikaz.short_description = "Vytvoriť platobný príkaz a krycí list pre THS"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_platobny_prikaz.allowed_permissions = ('change',)

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(VytvarnaObjednavkaPlatbaAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

# pripajanie suborov k objektu: krok 2, vytvoriť XxxSuborAdmin
# musí byť pred krokom 3
class PlatbaAutorskaSumarSuborAdmin(admin.StackedInline):
    model = PlatbaAutorskaSumarSubor

@admin.register(PlatbaAutorskaSumar)
class PlatbaAutorskaSumarAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin):
    form = PlatbaAutorskaSumarForm
    # určiť poradie polí v editovacom formulári
    fields = ['cislo', 'vyplatit_ths', 'podklady_odoslane', 'autori_na_vyplatenie', 'datum_uhradenia', 'vyplatene', 'kryci_list_odoslany', 'dan_zaplatena', 'datum_zalozenia', 'datum_oznamenia', 'import_rs', 'import_webrs', 'datum_importovania']
    list_display = ['cislo', 'podklady_odoslane', 'datum_uhradenia', 'kryci_list_odoslany', 'dan_zaplatena', 'datum_zalozenia', 'datum_oznamenia', 'datum_importovania', 'honorar_rs', 'honorar_webrs', 'honorar_spolu', 'vyplatene_spolu', 'odvod_LF', 'odvedena_dan']
    actions = ['vytvorit_podklady_pre_THS', 'zaznamenat_platby_do_db', 'zrusit_platbu']
    # pripajanie suborov k objektu: krok 3, inline do XxxAdmin 
    inlines = [PlatbaAutorskaSumarSuborAdmin]

    def get_inlines(self, request, obj):
        if obj and obj.platba_zaznamenana == AnoNie.ANO:
            return []
        else:
            return self.inlines

    #obj is None during the object creation, but set to the object being edited during an edit
    def get_readonly_fields(self, request, obj=None):
        fields = [f.name for f in PlatbaAutorskaSumar._meta.get_fields()]
        if obj:
            #Pole Podklady odoslané
            if obj.vyplatit_ths and not obj.datum_uhradenia: 
                fields.remove("podklady_odoslane")
            if obj.podklady_odoslane and not "podklady_odoslane" in fields:
                fields.append("podklady_odoslane")
            #Pole Vyplácaní autori
            if obj.podklady_odoslane and not obj.datum_uhradenia and "autori_na_vyplatenie" in fields:
                fields.remove("autori_na_vyplatenie")
            #Pole Vyplatené THS-kou
            if obj.podklady_odoslane and not obj.datum_uhradenia and "datum_uhradenia" in fields:
                fields.remove("datum_uhradenia")
            #Pole 'Krycí list' odoslaný:
            if obj.vyplatene and not obj.kryci_list_odoslany and "kryci_list_odoslany" in fields:
                fields.remove("kryci_list_odoslany")
            #Pole Založené do šanonov (po autoroch):
            if obj.vyplatene and not obj.dan_zaplatena and "dan_zaplatena" in fields:
                fields.remove("dan_zaplatena")
            #Pole Založené do šanonov (po autoroch):
            if obj.vyplatene and not obj.datum_zalozenia and "datum_zalozenia" in fields:
                fields.remove("datum_zalozenia")
            #Pole Oznámené FS (mesačné):
            if obj.vyplatene and not obj.datum_oznamenia and "datum_oznamenia" in fields:
                fields.remove("datum_oznamenia")
            #Pole Importované do RS/WEBRS:
            if obj.vyplatene and not obj.datum_importovania and "datum_importovania" in fields:
                fields.remove("datum_importovania")
        else:
            # V novej platbe povoliť len "cislo"
            fields.remove("cislo")
        return fields

    def honorar_spolu(self, sumplatba):
        platby = PlatbaAutorskaOdmena.objects.filter(cislo=sumplatba.cislo)
        odmeny = [platba.honorar for platba in platby]
        return sum(odmeny)

    def honorar_rs(self, sumplatba):
        platby = PlatbaAutorskaOdmena.objects.filter(cislo=sumplatba.cislo)
        odmeny = [platba.honorar_rs for platba in platby]
        return sum(odmeny)

    def honorar_webrs(self, sumplatba):
        platby = PlatbaAutorskaOdmena.objects.filter(cislo=sumplatba.cislo)
        odmeny = [platba.honorar_webrs for platba in platby]
        return sum(odmeny)

    def odvedena_dan(self, sumplatba):
        platby = PlatbaAutorskaOdmena.objects.filter(cislo=sumplatba.cislo)
        odmeny = [platba.odvedena_dan for platba in platby]
        return sum(odmeny)

    def odvod_LF(self, sumplatba):
        platby = PlatbaAutorskaOdmena.objects.filter(cislo=sumplatba.cislo)
        odmeny = [platba.odvod_LF for platba in platby]
        return sum(odmeny)

    def vyplatene_spolu(self, sumplatba):
        platby = PlatbaAutorskaOdmena.objects.filter(cislo=sumplatba.cislo)
        odmeny = [platba.uhradena_suma for platba in platby]
        return sum(odmeny)

    def zaznamenat_platby_do_db(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu platbu", messages.ERROR)
            return
        platba = queryset[0]
        #if platba.platba_zaznamenana == AnoNie.ANO:
            #self.message_user(request, f"Platba {platba.cislo} už bola vložená do databázy s dátumom vyplatenia {platba.datum_uhradenia}. Ak chcete platbu opakovane vložiť do databázy, musíte ju zrušit (odstrániť z databázy) pomocou 'Zrušiť záznam o platbe v databáze'", messages.ERROR)
            #return
        if not platba.datum_uhradenia:
            self.message_user(request, f"Platba nebola vložená do databázy, lebo nie je zadaný dátum jej vyplatenia THS-kou. ", messages.ERROR)
            return
        self.vyplatit_autorske_odmeny(request, platba)
        platba.platba_zaznamenana = AnoNie.ANO
        platba.datum_aktualizacie = timezone.now(),
        platba.save()
        pass
    zaznamenat_platby_do_db.short_description = PlatbaAutorskaSumar.zaznamenat_platby_do_db_name
    #Oprávnenie na použitie akcie, viazané na 'change'
    zaznamenat_platby_do_db.allowed_permissions = ('change',)

    def vytvorit_podklady_pre_THS(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu platbu", messages.ERROR)
            return
        platba = queryset[0]
        if platba.podklady_odoslane: 
            self.message_user(request, f"Platba {platba.cislo} už bola odoslaná na THS na vyplatenie {platba.podklady_odoslane}, akciu už nemožno použiť.", messages.ERROR)
            return
        if platba.platba_zaznamenana == AnoNie.ANO or platba.podklady_odoslane: 
            self.message_user(request, f"Platba {platba.cislo} už bola vložená do databázy s dátumom vyplatenia {platba.datum_uhradenia}. Akciu už nemožno použiť.", messages.ERROR)
            return
        self.vyplatit_autorske_odmeny(request, platba)
        platba.datum_aktualizacie = timezone.now(),
        platba.save()
        pass
    vytvorit_podklady_pre_THS.short_description = PlatbaAutorskaSumar.vytvorit_podklady_pre_THS_name
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_podklady_pre_THS.allowed_permissions = ('change',)

    def vyplatit_autorske_odmeny(self, request, platba):
        self.db_logger = logging.getLogger('db')

        #vytvoriť zoznam pripojených súborov
        subory = platba.platbaautorskasumarsubor_set.all()
        nazvy = [subor.file.name for subor in subory]
        try:
            # ak vytvárame finálny prehľad, platba.datum_uhradenia je vyplnené 
            if platba.datum_uhradenia:
                vao = VyplatitAutorskeOdmeny(nazvy, platba.cislo, 
                        platba.datum_uhradenia,
                        platba.autori_na_vyplatenie.split())
            else:
                vao = VyplatitAutorskeOdmeny(nazvy, platba.cislo)
            vao.vyplatit_odmeny()
            logs = vao.get_logs()
            #status, msg, vytvorene_subory = VyplatitAutorskeOdmeny(platba)
            for log in logs:
                fname = re.findall(r"uložené do súboru ({}[^ ]*)".format(settings.MEDIA_ROOT),log[1]) 
                if fname:
                    fname = fname[0].strip(".").replace(settings.MEDIA_ROOT,"")
                    if "THS" in fname:
                        platba.vyplatit_ths = fname
                    elif "Vyplatene" in fname:
                        platba.vyplatene = fname
                    elif "Import-rs" in fname:
                        platba.import_rs = fname
                    elif "Import-webrs" in fname:
                        platba.import_webrs = fname
                        
                self.message_user(request, log[1].replace(settings.MEDIA_ROOT,""), log[0])
            # prebrať a uložiť novovytvorený zoznam autorov (len pri akcii "Vytvoriť podklady na vyplatenie autorských odmien pre THS")
            if not platba.datum_uhradenia and vao.zoznam_autorov:
                platba.autori_na_vyplatenie = " ".join(vao.zoznam_autorov)

            if platba.datum_uhradenia:
                self.message_user(request, "Vygenerované boli finálne dokumenty platby, pokračujte podľa inštrukcií v jednotlivých poliach platby." , messages.WARNING)
            else:
                po = PlatbaAutorskaSumar.podklady_odoslane.field.verbose_name
                pv = PlatbaAutorskaSumar.vyplatit_ths.field.verbose_name
                self.message_user(request, f"Ak je platba pripravená na vyplatenie, odošlite platobný príkaz na vyplatenie honorárov podľa inštrukcií v poli '{pv}' a vyplňte pole '{po}'." , messages.WARNING)

            platba.save()
            #self.message_user(request, msg, status)
        except Exception as error:
            self.message_user(request, error, messages.ERROR)
        pass
        #for zmluva  in queryset:

    def zrusit_platbu(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu platbu", messages.ERROR)
            return
        platba = queryset[0]
        if platba.platba_zaznamenana == AnoNie.NIE: 
            self.message_user(request, f"Platbu {platba.cislo} nemožno zrušiť, lebo ešte nebola vložená do databázy", messages.ERROR)
            return
        vao = VyplatitAutorskeOdmeny()
        vao.zrusit_vyplacanie(platba.cislo)
        platba.datum_uhradenia = None
        platba.datum_importovania = None
        platba.datum_zalozenia = None
        platba.datum_oznamenia = None
        platba.autori_na_vyplatenie = None
        platba.platba_zaznamenana = AnoNie.NIE
        #odstrániť súbory
        platba.vyplatit_ths.delete()
        platba.vyplatene.delete()
        platba.import_rs.delete()
        platba.import_webrs.delete()
        platba.vyplatit_ths=None
        platba.vyplatene=None
        platba.import_rs=None
        platba.import_webrs=None
        platba.podklady_odoslane=None
        platba.kryci_list_odoslany=None
        platba.dan_zaplatena=None
        pass
        platba.save()
        logs = vao.get_logs()
        for log in logs:
            self.message_user(request, log[1].replace(settings.MEDIA_ROOT,""), log[0])
        #self.message_user(request, f"Platba {platba.cislo} bola zrušená", messages.INFO)
    zrusit_platbu.short_description = PlatbaAutorskaSumar.zrusit_platbu_name
    #Oprávnenie na použitie akcie, viazané na 'delete'
    zrusit_platbu.allowed_permissions = ('delete',)

    # Nastaviť počiatočnú hodnotu (netreba to spraviť v model)
    def get_changeform_initial_data(self, request):
        #return {'cislo': datetime.now().strftime('%Y-%m-%d')}
        return {'cislo': nasledujuce_cislo(PlatbaAutorskaSumar)}

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(PlatbaAutorskaSumarAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod


# pripajanie suborov k objektu: krok 4, register XxxSubor a definicia XxxSuborAdmin
@admin.register(PlatbaAutorskaSumarSubor)
class PlatbaAutorskaSumarSuborAdmin(admin.ModelAdmin):
    list_display = (["file", "platba_autorska_sumar"])
    def get_readonly_fields(self, request, obj=None):
        return ["platba_autorska_sumar", "file"]

@admin.register(SystemovySubor)
class SystemovySuborAdmin(admin.ModelAdmin):
    list_display = ("subor_nazov", "subor_popis", "subor")
    fields = ("subor_nazov", "subor_popis", "subor")
    # názov sa nesmie meniť, podľa názvu sa v kóde súbor vyhľadáva
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["subor_nazov"]
        else:
            return []

