from django.contrib import admin 
from django import forms
from django.utils import timezone
from django.contrib import messages
import re
from datetime import date, datetime, timedelta
from ipdb import set_trace as trace
from .models import EkonomickaKlasifikacia, TypZakazky, Zdroj, Program, Dodavatel, ObjednavkaZmluva, AutorskyHonorar
from .models import Objednavka, Zmluva, PrijataFaktura, SystemovySubor, Rozhodnutie, PrispevokNaStravne
from .models import Dohoda, DoVP, DoPC, DoBPS, VyplacanieDohod, AnoNie, PlatovyVymer
from .models import ZamestnanecDohodar, Zamestnanec, Dohodar
from .common import VytvoritPlatobnyPrikaz, VytvoritSuborDohody, VytvoritSuborObjednavky, leapdays
from .forms import PrijataFakturaForm, AutorskeZmluvyForm, ObjednavkaForm, ZmluvaForm, PrispevokNaStravneForm
from .forms import PlatovyVymerForm
from .forms import DoPCForm, DoVPForm, DoBPSForm, nasledujuce_cislo, VyplacanieDohodForm
from .rokydni import datum_postupu, vypocet_prax, vypocet_zamestnanie 

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

# Ak sa má v histórii zobraziť zoznam zmien, príslušná admin trieda musí dediť od ZobraziZmeny
class ZobrazitZmeny():
    # v histórii zobraziť zoznam zmenených polí
    history_list_display = ['changed_fields']
    def changed_fields(self, obj):
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            return ", ".join(delta.changed_fields)
        return None

@admin.register(Zdroj)
class ZdrojAdmin(ZobrazitZmeny, SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("kod", "popis")

@admin.register(Program)
class ProgramAdmin(ZobrazitZmeny, SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("kod", "popis")

@admin.register(TypZakazky)
class TypZakazkyAdmin(ZobrazitZmeny, SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("kod", "popis")

@admin.register(EkonomickaKlasifikacia)
class EkonomickaKlasifikaciaAdmin(ZobrazitZmeny, SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("kod", "nazov")
    search_fields = ("^kod", "nazov")

@admin.register(Dodavatel)
class DodavatelAdmin(ZobrazitZmeny, SimpleHistoryAdmin, ImportExportModelAdmin):
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

class ObjednavkaZmluvaAdmin(ZobrazitZmeny, ImportExportModelAdmin):
    resource_class = ObjednavkaZmluvaResource

@admin.register(Objednavka)
class ObjednavkaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    form = ObjednavkaForm
    list_display = ("cislo", "subor_objednavky", "datum_vytvorenia", "dodavatel_link","predmet")
    #def formfield_for_dbfield(self, db_field, **kwargs):
        #formfield = super(ObjednavkaAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        #if db_field.name == 'objednane_polozky':
            #formfield.widget = forms.Textarea(attrs=formfield.widget.attrs)
        #return formfield

    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["cislo", "predmet", "dodavatel__nazov"]
    actions = ['vytvorit_subor_objednavky']

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

    def vytvorit_subor_objednavky(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu objednavku", messages.ERROR)
            return
        objednavka = queryset[0]
        status, msg, vytvoreny_subor = VytvoritSuborObjednavky(objednavka)
        if status != messages.ERROR:
            objednavka.subor_objednavky = vytvoreny_subor
            objednavka.save()
            pass
        self.message_user(request, msg, status)

    vytvorit_subor_objednavky.short_description = "Vytvoriť súbor objednavky"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_subor_objednavky.allowed_permissions = ('change',)

@admin.register(Rozhodnutie)
class RozhodnutieAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
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
class ZmluvaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
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
#class PrijataFakturaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
class PrijataFakturaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = PrijataFakturaForm
    list_display = ["cislo", "objednavka_zmluva_link", "prijata_faktura", "suma", "platobny_prikaz", "dane_na_uhradu", "zdroj", "program", "zakazka", "ekoklas"]
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

#class AutorskyHonorarAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
class AutorskyHonorarAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
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
class PrispevokNaStravneAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
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
class SystemovySuborAdmin(ZobrazitZmeny, admin.ModelAdmin):
    list_display = ("subor_nazov", "subor_popis", "subor")
    fields = ("subor_nazov", "subor_popis", "subor")
    # názov sa nesmie meniť, podľa názvu sa v kóde súbor vyhľadáva
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["subor_nazov"]
        else:
            return []

@admin.register(ZamestnanecDohodar)
class ZamestnanecDohodar(AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("priezvisko", "meno", "rod_priezvisko", "email", "rodne_cislo", "datum_nar", "miesto_nar", "adresa", "_dochodok", "_ztp","poistovna", "cop", "stav")
    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["priezvisko", "meno"]
    def adresa(self, obj):
        if obj.adresa_mesto:
            return f"{obj.adresa_ulica} {obj.adresa_mesto}, {obj.adresa_stat}".strip()
    def _dochodok(self, obj):
        if obj.poberatel_doch == AnoNie.ANO:
            return f"{obj.typ_doch}, {obj.datum_doch}".strip()
        else:
            return "Nie"
    _dochodok.short_description = "Dôchodok"
    def _ztp(self, obj):
        if obj.ztp == AnoNie.ANO:
            return f"Áno, {obj.datum_ztp}".strip()
        else:
            return "Nie"
    _ztp.short_description = "ZŤP"
    def _roky_dni(self, obj):
        return f"{obj.zapocitane_roky}, {obj.zapocitane_dni}".strip()
    _roky_dni.short_description = "Započítaná prax"


@admin.register(Dohodar)
class Dohodar(AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("priezvisko", "meno", "rod_priezvisko", "email", "rodne_cislo", "datum_nar", "miesto_nar", "adresa", "_dochodok", "_ztp","poistovna", "cop", "stav")
    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["priezvisko", "meno"]
    def adresa(self, obj):
        if obj.adresa_mesto:
            return f"{obj.adresa_ulica} {obj.adresa_mesto}, {obj.adresa_stat}".strip()
    def _dochodok(self, obj):
        if obj.poberatel_doch == AnoNie.ANO:
            return f"{obj.typ_doch}, {obj.datum_doch}".strip()
        else:
            return "Nie"
    _dochodok.short_description = "Dôchodok"
    def _ztp(self, obj):
        if obj.ztp == AnoNie.ANO:
            return f"Áno, {obj.datum_ztp}".strip()
        else:
            return "Nie"
    _ztp.short_description = "ZŤP"


@admin.register(Zamestnanec)
class Zamestnanec(AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("priezvisko", "meno", "cislo_zamestnanca", "zamestnanie_od", "_roky_dni", "rod_priezvisko", "email", "rodne_cislo", "datum_nar", "miesto_nar", "adresa", "_dochodok", "_ztp","poistovna", "cop", "stav")
    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["priezvisko", "meno"]
    def adresa(self, obj):
        if obj.adresa_mesto:
            return f"{obj.adresa_ulica} {obj.adresa_mesto}, {obj.adresa_stat}".strip()
    adresa.short_description = "Adresa"
    def _dochodok(self, obj):
        if obj.poberatel_doch == AnoNie.ANO:
            return f"{obj.typ_doch}, {obj.datum_doch}".strip()
        else:
            return "Nie"
    _dochodok.short_description = "Dôchodok"
    def _ztp(self, obj):
        if obj.ztp == AnoNie.ANO:
            return f"Áno, {obj.datum_ztp}".strip()
        else:
            return "Nie"
    _ztp.short_description = "ZŤP"
    def _roky_dni(self, obj):
        return f"{obj.zapocitane_roky}.{obj.zapocitane_dni}".strip()
    _roky_dni.short_description = "Započítaná prax (roky.dni)"


@admin.register(DoVP)
class DoVPAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = DoVPForm
    fields = ["cislo", "zmluvna_strana", "vynimka", "_predmet", "id_tsh", "datum_od", "datum_do", "odmena_celkom", "hod_celkom", "pomocnik", "subor_dohody", "poznamka","zdroj", "program", "zakazka", "ekoklas" ]
    list_display = ("cislo","id_tsh",  "zmluvna_strana_link", "vyplatene", "_predmet", "vynimka", "subor_dohody", "odmena_celkom", "hod_celkom", "datum_od", "datum_do", "poznamka" )

    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["cislo", "zmluvna_strana__priezvisko"]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('zmluvna_strana', {
            'admin_order_field': 'zmluvna_strana__priezvisko', # Allow to sort members by the column
        })
    ]
    list_totals = [
        ('odmena_celkom', Sum),
    ]

    def _predmet(self, obj):
        if obj:
            return obj.predmet if len(obj.predmet) < 60 else f"{obj.predmet[:60]}..."
    _predmet.short_description = "Pracovná činnosť                             " # nezalomiteľné medzery ...

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

@admin.register(DoBPS)
class DoBPSAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = DoBPSForm
    fields = ["cislo", "zmluvna_strana", "vynimka", "predmet", "subor_dohody", "datum_od", "datum_do", "datum_ukoncenia", "odmena_celkom", "poznamka","zdroj", "program", "zakazka", "ekoklas" ]
    list_display = ("cislo", "zmluvna_strana_link", "vyplatene", "_predmet", "vynimka", "subor_dohody", "odmena_celkom", "datum_od", "datum_do", "datum_ukoncenia", "poznamka" )

    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["cislo", "zmluvna_strana__priezvisko"]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('zmluvna_strana', {
            'admin_order_field': 'zmluvna_strana__priezvisko', # Allow to sort members by the column
        })
    ]
    list_totals = [
        ('odmena_celkom', Sum),
    ]

    def _predmet(self, obj):
        if obj:
            return obj.predmet if len(obj.predmet) < 60 else f"{obj.predmet[:60]}..."
    _predmet.short_description = "Pracovná činnosť                             " # nezalomiteľné medzery ...

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

@admin.register(DoPC)
class DoPCAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = DoPCForm
    fields = ["cislo", "zmluvna_strana", "vynimka", "predmet", "subor_dohody", "datum_od", "datum_do", "datum_ukoncenia", "odmena_mesacne", "hod_mesacne", "poznamka","zdroj", "program", "zakazka", "ekoklas" ]
    list_display = ("cislo", "zmluvna_strana_link", "vyplatene", "_predmet", "vynimka", "subor_dohody", "odmena_mesacne", "hod_mesacne", "datum_od", "datum_do", "datum_ukoncenia", "poznamka" )

    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["cislo", "zmluvna_strana__priezvisko"]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('zmluvna_strana', {
            'admin_order_field': 'zmluvna_strana__priezvisko', # Allow to sort members by the column
        })
    ]
    list_totals = [
        ('odmena_mesacne', Sum),
    ]
    actions = ['vytvorit_subor_dohody']

    def _predmet(self, obj):
        if obj:
            return obj.predmet if len(obj.predmet) < 60 else f"{obj.predmet[:60]}..."
    _predmet.short_description = "Pracovná činnosť                             " # nezalomiteľné medzery ...

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
class VyplacanieDohodAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = VyplacanieDohodForm
    list_display = ["datum_vyplatenia", "dohoda_link", "vyplatena_odmena", "poistne_zamestnavatel", "poistne_dohodar", "dan_dohodar", "na_ucet"]
    search_fields = ["dohoda__cislo", "dohoda__zmluvna_strana__priezvisko"]
    list_totals = [
        ('vyplatena_odmena', Sum),
        ('poistne_dohodar', Sum),
        ('poistne_zamestnavatel', Sum),
        ('dan_dohodar', Sum),
        ('na_ucet', Sum)
    ]
    #"poistne_zamestnavatel", "poistne_dohodar", "dan_dohodar", "vyplatena_odmena",

    # zoraďovateľný odkaz na dodávateľa
    change_links = [
        ('dohoda', {
            'admin_order_field': 'dohoda__cislo', # Allow to sort members by the column
        })
    ]

    def get_readonly_fields(self, request, obj=None):
        fields = [f.name for f in VyplacanieDohod._meta.get_fields()]
        fields.remove("id")
        if not obj:
            fields.remove("dohoda")
            fields.remove("datum_vyplatenia")
            fields.remove("vyplatena_odmena")
        return fields

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(VyplacanieDohodAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

@admin.register(PlatovyVymer)
class PlatovyVymerAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin):
    form = PlatovyVymerForm
    list_display = ["mp","cislo_zamestnanca", "zamestnanec_link", "zamestnanie_od", "zapocitane", "datum_postup", "datum_od", "datum_do", "_prax_roky_dni", "_zamestnanie_roky_dni", "tarifny_plat", "osobny_priplatok", "funkcny_priplatok",  "platova_trieda", "platovy_stupen", "suborvymer"]
    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["zamestnanec__meno", "zamestnanec__priezvisko"]
    actions = ['duplikovat_zaznam']

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('zamestnanec', {
            'admin_order_field': 'zamestnanec__priezvisko', # Allow to sort members by the column
        })
    ]

    def get_readonly_fields(self, request, obj=None):
        if obj.datum_do:
            aux = [f.name for f in PlatovyVymer._meta.get_fields()]
            aux.remove("datum_do")
            return aux
        else:
            return ["praxroky", "praxdni", "zamestnanieroky", "zamestnaniedni", "datum_postup"]

    def zamestnanie_od(self, obj):
        return obj.zamestnanec.zamestnanie_od.strftime('%d. %m. %Y')

    def zapocitane(self, obj):
        return f"{obj.zamestnanec.zapocitane_roky}r {obj.zamestnanec.zapocitane_dni}d".strip() 

    def mp(self, obj):
        if obj.zamestnanec:
            od = obj.datum_od.strftime('%d. %m. %Y') if obj.datum_od else '--'
            return f"{obj.zamestnanec.priezvisko}, {od}".strip()
    mp.short_description = "Výmer"

    def _prax_roky_dni(self, obj):
        #return f"{obj.praxroky}, {obj.praxdni}".strip()
        #return f"{obj.praxroky}r {obj.praxdni}d".strip()
        return f"{obj.praxroky}r {obj.praxdni}d".strip() if obj.praxroky or obj.praxdni else "-"
    _prax_roky_dni.short_description = "Celková prax"

    def _zamestnanie_roky_dni(self, obj):
        #return f"{obj.zamestnanieroky}, {obj.zamestnaniedni}".strip()
        return f"{obj.zamestnanieroky}r {obj.zamestnaniedni}d".strip() if obj.zamestnanieroky or obj.zamestnaniedni else "-"
    _zamestnanie_roky_dni.short_description = "Zamestnanie v EnÚ"

    #ukončí platnosť starého výmeru a aktualizuje prax
    def save_model(self, request, obj, form, change):
        if obj.datum_do:    # ukončený prac. pomer, aktualizovať prax
            # rok praxe sa ráta ako 365 dní, t. j. po odpracovaní 10 rokov sa roky praxe zvýšia o 10 a dni sa nezmenia
            years, days = vypocet_zamestnanie(obj.zamestnanec.zamestnanie_od, obj.datum_do)
            obj.zamestnanieroky = years
            obj.zamestnaniedni = days
            years, days = vypocet_prax(
                    obj.zamestnanec.zamestnanie_od, 
                    obj.datum_do, 
                    (obj.zamestnanec.zapocitane_roky, obj.zamestnanec.zapocitane_dni)
                    ) 
            obj.praxroky = years 
            obj.praxdni = days
            obj.datum_postup = None
        else:               #vytvorený nový výmer
            # nájsť najnovší starý výmer s nevyplneným poľom datum_do
            query_set = PlatovyVymer.objects.filter(cislo_zamestnanca=obj.cislo_zamestnanca).filter(datum_do__isnull=True)
            #Vylúčiť aktuálny objekt
            qset = [q for q in query_set if q != obj] 
            if qset:
                stary = qset[0]
                # ukonciť platnosť starého nastavením datum_do
                stary.datum_do = obj.datum_od-timedelta(1)
                # aktualizácia praxe v stary, hodnotu použiť aj v aktuálnom
                years, days = vypocet_zamestnanie(obj.zamestnanec.zamestnanie_od, stary.datum_do)
                stary.zamestnanieroky = years
                stary.zamestnaniedni = days
                years, days = vypocet_prax(
                        obj.zamestnanec.zamestnanie_od, 
                        stary.datum_do, 
                        (obj.zamestnanec.zapocitane_roky, obj.zamestnanec.zapocitane_dni)
                        ) 
                stary.praxroky = years 
                stary.praxdni = days
                stary.datum_postup = None
                stary.save()
                pass
            dp = datum_postupu(
                    obj.zamestnanec.zamestnanie_od, 
                    date.today(), 
                    (obj.zamestnanec.zapocitane_roky, obj.zamestnanec.zapocitane_dni)
                    )
            print("vymer2: ",obj.zamestnanec.zamestnanie_od, obj.zamestnanec.zapocitane_roky, obj.zamestnanec.zapocitane_dni,  dp)
            obj.datum_postup = dp[1] if dp else None
        super(PlatovyVymerAdmin, self).save_model(request, obj, form, change)

    def duplikovat_zaznam(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jeden výmer.", messages.ERROR)
            return
        star = queryset[0]
        if star.datum_do:
            self.message_user(request, f"Tento výmer nie je aktuálny. Duplikovať možno len aktuálny výmer.", messages.ERROR)
            return
        novy = PlatovyVymer.objects.create(
                cislo_zamestnanca = star.cislo_zamestnanca,
                zamestnanec = star.zamestnanec,
                tarifny_plat = star.tarifny_plat,
                osobny_priplatok = star.osobny_priplatok,
                funkcny_priplatok = star.funkcny_priplatok,
                platova_trieda = star.platova_trieda,
                platovy_stupen = star.platovy_stupen,
                uvazok = star.uvazok,
                program = star.program,
                ekoklas = star.ekoklas,
                zakazka = star.zakazka,
                zdroj = star.zdroj
                #polia praxroky, praxdni, zamestnanieroky, zamestnaniedni sa neduplikuju (sú dopĺňané automaticky pri ukladaní) 
            )
        novy.save()
        self.message_user(request, f"Vytvorený bol nový platobný výmer pre {star.zamestnanec}.", messages.SUCCESS)

    duplikovat_zaznam.short_description = "Duplikovať platobný výmer"
    #Oprávnenie na použitie akcie, viazané na 'change'
    duplikovat_zaznam.allowed_permissions = ('change',)
