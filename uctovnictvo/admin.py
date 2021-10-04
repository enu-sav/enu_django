from django.contrib import admin 
from django import forms
from django.utils import timezone
from django.contrib import messages
import re
from datetime import datetime
from ipdb import set_trace as trace
from .models import EkonomickaKlasifikacia, TypZakazky, Zdroj, Program, Dodavatel, ObjednavkaZmluva, AutorskyHonorar
from .models import Objednavka, Zmluva, PrijataFaktura, SystemovySubor, Rozhodnutie, PrispevokNaStravne
from .models import Dohoda, DoVP, DoPC, Dohodar, VyplacanieDohod
from .common import VytvoritPlatobnyPrikaz, VytvoritSuborDohody
from .forms import PrijataFakturaForm, AutorskeZmluvyForm, ObjednavkaForm, ZmluvaForm, PrispevokNaStravneForm
from .forms import DoPCForm, DoVPForm, nasledujuce_cislo

#zobrazenie histórie
#https://django-simple-history.readthedocs.io/en/latest/admin.html
from simple_history.admin import SimpleHistoryAdmin

from import_export.admin import ImportExportModelAdmin
from import_export import resources

#from totalsum.admin import TotalsumAdmin

# potrebné pre súčty, https://github.com/douwevandermeij/admin-totals
# upravená šablóna admin_totals/change_list_results_totals.html
from admin_totals.admin import ModelAdminTotals
from django.db.models import Sum

#umožniť zobrazenie autora v zozname zmlúv
#https://pypi.org/project/django-admin-relation-links/
from django_admin_relation_links import AdminChangeLinksMixin

@admin.register(Zdroj)
class ZdojAdmin(SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("kod", "popis")

@admin.register(Program)
class ProgramAdmin(SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("kod", "popis")

@admin.register(TypZakazky)
class TypZakazkyAdmin(SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("kod", "popis")

@admin.register(EkonomickaKlasifikacia)
class EkonomickaKlasifikaciaAdmin(SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("kod", "nazov")
    search_fields = ("^kod", "nazov")

@admin.register(Dodavatel)
class DodavatelAdmin(SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("nazov", "s_danou", "bankovy_kontakt", "adresa") 
    search_fields = ("nazov",)
    def adresa(self, obj):
        if obj.adresa_mesto:
            return f"{obj.adresa_ulica} {obj.adresa_mesto}, {obj.adresa_stat}".strip()
    adresa.short_description = "Adresa"

class ObjednavkaZmluvaResource(resources.ModelResource):
    class Meta:
        model = ObjednavkaZmluva
        import_id_fields = ('cislo',)
        fields = ('cislo', 'dodavatel', 'predmet', 'poznamka')

class ObjednavkaZmluvaAdmin(ImportExportModelAdmin):
    resource_class = ObjednavkaZmluvaResource

@admin.register(Objednavka)
class ObjednavkaAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    form = ObjednavkaForm
    list_display = ("cislo", "datum_vytvorenia", "dodavatel_link","predmet", )
    #def formfield_for_dbfield(self, db_field, **kwargs):
        #formfield = super(ObjednavkaAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        #if db_field.name == 'objednane_polozky':
            #formfield.widget = forms.Textarea(attrs=formfield.widget.attrs)
        #return formfield

    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["cislo", "predmet", "dodavatel__nazov"]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('dodavatel', {
            'admin_order_field': 'dodavatel__nazov', # Allow to sort members by the `dodavatel_link` column
        })
    ]

    #obj is None during the object creation, but set to the object being edited during an edit
    def get_readonly_fields(self, request, obj=None):
        return ["cislo"] if obj else []

@admin.register(Rozhodnutie)
class RozhodnutieAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("cislo", "predmet", "dodavatel_link", "poznamka" )

    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["cislo", "dodavatel__nazov"]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('dodavatel', {
            'admin_order_field': 'dodavatel__nazov', # Allow to sort members by the `dodavatel_link` column
        })
    ]

@admin.register(Zmluva)
class ZmluvaAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    form = ZmluvaForm
    list_display = ["cislo", "dodavatel_link", "predmet", "datum_zverejnenia_CRZ", "url_zmluvy_html"]
    search_fields = ["dodavatel__nazov", "cislo", "predmet"]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('dodavatel', {
            'admin_order_field': 'dodavatel__nazov', # Allow to sort members by the `dodavatel_link` column
        })
    ]

    # formátovať pole url_zmluvy
    def url_zmluvy_html(self, obj):
        from django.utils.html import format_html
        if obj.url_zmluvy:
            return format_html(f'<a href="{obj.url_zmluvy}" target="_blank">pdf</a>')
        else:
            return None
    url_zmluvy_html.short_description = "Zmluva v CRZ"

@admin.register(PrijataFaktura)
#medzi  ModelAdminTotals a ImportExportModelAdmin je konflikt
#zobrazia sa Import Export tlačidlá alebo súčty
#class PrijataFakturaAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
class PrijataFakturaAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = PrijataFakturaForm
    list_display = ["cislo", "objednavka_zmluva_link", "suma", "platobny_prikaz", "dane_na_uhradu", "zdroj", "program", "zakazka", "ekoklas"]
    search_fields = ["objednavka_zmluva__dodavatel__nazov", "^zdroj__kod", "^program__kod", "^zakazka__kod", "^ekoklas__kod" ]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    # Vyžaduje, aby ObjednavkaZmluva zmluva bola PolymorphicModel
    change_links = [
        ('objednavka_zmluva', {
            'label': "Objednávka, zmluva, rozhodnutie",
            'admin_order_field': 'objednavka_zmluva__cislo', # Allow to sort members by the `xxx_link` column
        })
    ] 
    list_totals = [
        ('suma', Sum),
    ]
    actions = ['vytvorit_platobny_prikaz', 'duplikovat_zaznam']

    #obj is None during the object creation, but set to the object being edited during an edit
    #"platobny_prikaz" je generovaný, preto je vźdy readonly
    def get_readonly_fields(self, request, obj=None):
        return ["platobny_prikaz"]

    def vytvorit_platobny_prikaz(self, request, queryset):
        for faktura in queryset:
            status, msg, vytvoreny_subor = VytvoritPlatobnyPrikaz(faktura)
            if status != messages.ERROR:
                faktura.dane_na_uhradu = timezone.now()
                faktura.platobny_prikaz = vytvoreny_subor
                faktura.save()
            self.message_user(request, msg, status)

    vytvorit_platobny_prikaz.short_description = "Vytvoriť platobný príkaz a krycí list pre THS"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_platobny_prikaz.allowed_permissions = ('change',)

    def duplikovat_zaznam(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu faktúru", messages.ERROR)
            return
        stara = queryset[0]
        nc = nasledujuce_cislo(PrijataFaktura)
        nova_faktura = PrijataFaktura.objects.create(
                cislo = nc,
                program = stara.program,
                ekoklas = stara.ekoklas,
                zakazka = stara.zakazka,
                zdroj = stara.zdroj,
                predmet = stara.predmet,
                objednavka_zmluva = stara.objednavka_zmluva
            )
        nova_faktura.save()
        self.message_user(request, f"Vytvorená bola nová faktúra dodávateľa {nova_faktura.objednavka_zmluva.dodavatel.nazov} číslo {nc}.", messages.SUCCESS)

    duplikovat_zaznam.short_description = "Duplikovať faktúru"
    #Oprávnenie na použitie akcie, viazané na 'change'
    duplikovat_zaznam.allowed_permissions = ('change',)

    def save_model(self, request, obj, form, change):
        if 'suma' in form.changed_data:
            if obj.suma > 0:
                messages.add_message(request, messages.WARNING, "Do poľa 'suma' sa obvykle vkladajú výdavky (záporná suma), vložili ste však kladnú hodnotu sumy. Ak ide o omyl, hodnotu opravte.") 
        super(PrijataFakturaAdmin, self).save_model(request, obj, form, change)

@admin.register(AutorskyHonorar)

#class AutorskyHonorarAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
class AutorskyHonorarAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = AutorskeZmluvyForm
    list_display = ["cislo", "suma", "suma_lf", "suma_dan"]
    # určiť poradie poli v editovacom formulári
    fields = ["cislo", "suma", "suma_lf", "suma_dan", "zdroj", "program", "zakazka", "ekoklas"]

    list_totals = [
        ('suma', Sum),
        ('suma_lf', Sum),
        ('suma_dan', Sum),
    ]

@admin.register(PrispevokNaStravne)
class PrispevokNaStravneAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = PrispevokNaStravneForm
    list_display = ["cislo", "suma_zamestnavatel", "suma_socfond"]
    # určiť poradie poli v editovacom formulári
    fields = ["cislo", "suma_zamestnavatel", "suma_socfond", "zdroj", "program", "zakazka", "ekoklas" ]

    list_totals = [
        ('suma_zamestnavatel', Sum),
        ('suma_socfond', Sum),
    ]
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [ "program", "ekoklas", "zakazka", "zdroj"]
        else:
            return []

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

@admin.register(Dohodar)
class DohodarAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("priezvisko", "meno", "rod_priezvisko", "email", "rodne_cislo", "datum_nar", "miesto_nar", "adresa", "poberatel_doch", "typ_doch", "poistovna", "cop")
    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["priezvisko", "meno"]
    def adresa(self, obj):
        if obj.adresa_mesto:
            return f"{obj.adresa_ulica} {obj.adresa_mesto}, {obj.adresa_stat}".strip()
    def save_model(self, request, obj, form, change):
        if 'poberatel_doch' in form.changed_data:
            if obj.poberatel_doch == AnoNie.ANO and not obj.typ_doch:
                messages.add_message(request, messages.WARNING, "sumy. Ak ide o omyl, hodnotu opravte.") 
        super(PrijataFakturaAdmin, self).save_model(request, obj, form, change)

@admin.register(DoVP)
class DoVPAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = DoVPForm
    fields = ["cislo", "zmluvna_strana", "predmet", "datum_od", "datum_do", "odmena_celkom", "poznamka","zdroj", "program", "zakazka", "ekoklas" ]
    list_display = ("cislo", "zmluvna_strana_link", "predmet", "odmena_celkom", "datum_od", "datum_do", "poznamka" )

    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["cislo", "zmluvna_strana__nazov"]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('zmluvna_strana', {
            'admin_order_field': 'zmluvna_strana__nazov', # Allow to sort members by the `zmluvna_strana_link` column
        })
    ]
    list_totals = [
        ('odmena_celkom', Sum),
    ]

@admin.register(DoPC)
class DoPCAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = DoPCForm
    fields = ["cislo", "zmluvna_strana", "predmet", "subor_dohody", "datum_od", "datum_do", "odmena_hod", "hod_tyzden", "odmena_celkom", "poznamka","zdroj", "program", "zakazka", "ekoklas" ]
    list_display = ("cislo", "zmluvna_strana_link", "predmet", "subor_dohody", "odmena_celkom", "odmena_hod", "hod_tyzden", "datum_od", "datum_do", "poznamka" )

    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["cislo", "zmluvna_strana__nazov"]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('zmluvna_strana', {
            'admin_order_field': 'zmluvna_strana__nazov', # Allow to sort members by the `zmluvna_strana_link` column
        })
    ]
    list_totals = [
        ('odmena_celkom', Sum),
    ]
    actions = ['vytvorit_subor_dohody']

    def vytvorit_subor_dohody(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu dohodu", messages.ERROR)
            return
        dohoda = queryset[0]
        status, msg, vytvoreny_subor = VytvoritSuborDohody(dohoda)
        if status != messages.ERROR:
            dohoda.subor_dohody = vytvoreny_subor
            dohoda.save()
            pass
        self.message_user(request, msg, status)

    vytvorit_subor_dohody.short_description = "Vytvoriť súbor dohody"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_subor_dohody.allowed_permissions = ('change',)

@admin.register(VyplacanieDohod)
class DoPCAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    list_display = ["dohoda", "vyplatena_odmena", "datum_vyplatenia"]
    search_fields = ["dohoda__cislo", "dohoda__zmluvna_strana__priezvisko"]
    list_totals = [
        ('vyplatena_odmena', Sum),
    ]

