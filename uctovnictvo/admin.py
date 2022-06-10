from django.contrib import admin 
from django import forms
from django.utils import timezone
from django.contrib import messages
from django.utils.html import format_html
from django.utils.safestring import mark_safe
import re
from datetime import date, datetime, timedelta
from ipdb import set_trace as trace
from .models import EkonomickaKlasifikacia, TypZakazky, Zdroj, Program, Dodavatel, ObjednavkaZmluva
from .models import Objednavka, Zmluva, PrijataFaktura, SystemovySubor, Rozhodnutie, PrispevokNaStravne
from .models import Dohoda, DoVP, DoPC, DoBPS, VyplacanieDohod, AnoNie, PlatovyVymer, StavVymeru
from .models import ZamestnanecDohodar, Zamestnanec, Dohodar, StavDohody, PravidelnaPlatba
from .models import Najomnik, NajomnaZmluva, NajomneFaktura, TypPP, TypPN, Cinnost
from .models import InternyPartner, InternyPrevod, Nepritomnost, RozpoctovaPolozka, RozpoctovaPolozkaDotacia
from .common import VytvoritPlatobnyPrikaz, VytvoritSuborDohody, VytvoritSuborObjednavky, leapdays, VytvoritKryciList
from .common import VytvoritPlatobnyPrikazIP
from .forms import PrijataFakturaForm, AutorskeZmluvyForm, ObjednavkaForm, ZmluvaForm, PrispevokNaStravneForm, PravidelnaPlatbaForm
from .forms import PlatovyVymerForm, NajomneFakturaForm, NajomnaZmluvaForm
from .forms import DoPCForm, DoVPForm, DoBPSForm, nasledujuce_cislo, VyplacanieDohodForm
from .forms import InternyPrevodForm, NepritomnostForm, RozpoctovaPolozkaDotaciaForm
from .rokydni import datum_postupu, vypocet_prax, vypocet_zamestnanie, postup_roky, roky_postupu
from beliana.settings import DPH
from dennik.models import Dokument, TypDokumentu, InOut

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

#https://pypi.org/project/django-admin-export-action/
from admin_export_action.admin import export_selected_objects

# Ak sa má v histórii zobraziť zoznam zmien, príslušná admin trieda musí dediť od ZobraziZmeny
class ZobrazitZmeny():
    # v histórii zobraziť zoznam zmenených polí
    history_list_display = ['changed_fields']
    def changed_fields(self, obj):
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            return ", ".join(delta.changed_fields)
        return None
    #stránkovanie a 'Zobraziť všetko'
    list_per_page = 50
    list_max_show_all = 100000

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

@admin.register(Cinnost)
class CinnostAdmin(ZobrazitZmeny, SimpleHistoryAdmin, ImportExportModelAdmin):
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

@admin.register(InternyPartner)
class InternyPartnerAdmin(ZobrazitZmeny, SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("nazov", "bankovy_kontakt", "adresa") 
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
    list_display = ("cislo", "subor_objednavky", "subor_prilohy", "datum_vytvorenia", "termin_dodania", "dodavatel_link","predmet")
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
    actions = [export_selected_objects]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('dodavatel', {
            'admin_order_field': 'dodavatel__nazov', # Allow to sort members by the `dodavatel_link` column
        })
    ]

    # formátovať pole url_zmluvy
    def url_zmluvy_html(self, obj):
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
    list_display = ["cislo", "objednavka_zmluva_link", "prijata_faktura", "suma", "predmet", "platobny_prikaz", "dane_na_uhradu", "zdroj", "zakazka", "ekoklas","cinnost"]
    search_fields = ["^cislo","objednavka_zmluva__dodavatel__nazov", "predmet", "^zdroj__kod", "^zakazka__kod", "^ekoklas__kod", "ekoklas__nazov",  "cinnost__kod", "cinnost__nazov" ]

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
    #"platobny_prikaz" je generovaný, preto je vždy readonly
    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return ["program", "platobny_prikaz", "dane_na_uhradu"]
        elif obj.dane_na_uhradu:
            nearly_all = ["program", "platobny_prikaz", "doslo_datum"] 
            nearly_all += ["splatnost_datum", "predmet", "suma", "mena", "objednavka_zmluva", "dane_na_uhradu"]
            return nearly_all
        elif not obj.platobny_prikaz:   #ešte nebola spustená akcia
            return ["program", "cislo", "platobny_prikaz", "dane_na_uhradu"]
        else:   #všetko hotové, možno odoslať, ale stále možno aj editovať
            return ["program", "cislo", "platobny_prikaz"]

    def vytvorit_platobny_prikaz(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu položku", messages.ERROR)
            return
        faktura = queryset[0]
        if faktura.dane_na_uhradu:
            self.message_user(request, f"Faktúra už bola daná na úhradu, vytváranie platobného príkazu nie je možné", messages.ERROR)
            return
        status, msg, vytvoreny_subor = VytvoritPlatobnyPrikaz(faktura, request.user)
        if status != messages.ERROR:
            #faktura.dane_na_uhradu = timezone.now()
            faktura.platobny_prikaz = vytvoreny_subor
            faktura.save()
        self.message_user(request, msg, status)

    vytvorit_platobny_prikaz.short_description = "Vytvoriť platobný príkaz a krycí list pre THS"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_platobny_prikaz.allowed_permissions = ('change',)

    def duplikovat_zaznam(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu položku", messages.ERROR)
            return
        stara = queryset[0]
        if not stara.dane_na_uhradu:
            self.message_user(request, f"Faktúra {stara.cislo} ešte nebola daná na uhradenie. Duplikovať možno len uhradené faktúry.", messages.ERROR)
            return
        nc = nasledujuce_cislo(PrijataFaktura)
        nova_faktura = PrijataFaktura.objects.create(
                cislo = nc,
                program = Program.objects.get(id=4),    #nealokovaný
                ekoklas = stara.ekoklas,
                zakazka = stara.zakazka,
                zdroj = stara.zdroj,
                cinnost = stara.cinnost,
                predmet = stara.predmet,
                objednavka_zmluva = stara.objednavka_zmluva
            )
        nova_faktura.save()
        self.message_user(request, f"Vytvorená bola nová faktúra dodávateľa '{nova_faktura.objednavka_zmluva.dodavatel.nazov}' číslo '{nc}', aktualizujte polia", messages.SUCCESS)
        vec = f"Faktúra {nc}"
        cislo_posta = nasledujuce_cislo(Dokument)
        dok = Dokument(
            cislo = cislo_posta,
            cislopolozky = nc,
            datumvytvorenia = date.today(),
            typdokumentu = TypDokumentu.FAKTURA,
            inout = InOut.PRIJATY,
            adresat = stara.adresat(),
            #vec = f'<a href="{self.instance.platobny_prikaz.url}">{vec}</a>',
            vec = vec,
            prijalodoslal=request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
        )
        dok.save()
        messages.warning(request, 
            format_html(
                'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>, treba v ňom doplniť údaje o prijatí.',
                mark_safe(f'<a href="/admin/dennik/dokument/{dok.id}/change/">{cislo_posta}</a>'),
                vec
                )
        )

    duplikovat_zaznam.short_description = "Duplikovať faktúru"
    #Oprávnenie na použitie akcie, viazané na 'change'
    duplikovat_zaznam.allowed_permissions = ('change',)

    def save_model(self, request, obj, form, change):
        #Ak sa vytvára nový záznam, do denníka pridať záznam o prijatej pošte
        if not PrijataFaktura.objects.filter(cislo=obj.cislo):  #Faktúra ešte nie je v databáze
            vec = f"Faktúra {obj.cislo}"
            cislo_posta = nasledujuce_cislo(Dokument)
            dok = Dokument(
                cislo = cislo_posta,
                cislopolozky = obj.cislo,
                #datumvytvorenia = self.cleaned_data['doslo_datum'],
                datumvytvorenia = date.today(),
                typdokumentu = TypDokumentu.FAKTURA,
                inout = InOut.PRIJATY,
                adresat = obj.adresat(),
                #vec = f'<a href="{self.instance.platobny_prikaz.url}">{vec}</a>',
                vec = vec,
                prijalodoslal=request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
            )
            dok.save()
            messages.warning(request, 
                format_html(
                    'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>, treba v ňom doplniť údaje o prijatí.',
                    mark_safe(f'<a href="/admin/dennik/dokument/{dok.id}/change/">{cislo_posta}</a>'),
                    vec
                    )
            )
            pass
        if 'suma' in form.changed_data:
            if obj.suma >= 0:
                messages.add_message(request, messages.WARNING, "Do poľa 'suma' sa obvykle vkladajú výdavky (záporná suma), vložili ste však 0 alebo kladnú hodnotu sumy. Ak ide o omyl, hodnotu opravte.") 
        super(PrijataFakturaAdmin, self).save_model(request, obj, form, change)

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(PrijataFakturaAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

@admin.register(PravidelnaPlatba)
#medzi  ModelAdminTotals a ImportExportModelAdmin je konflikt
#zobrazia sa Import Export tlačidlá alebo súčty
#class PravidelnaPlatbaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
class PravidelnaPlatbaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = PravidelnaPlatbaForm
    list_display = ["cislo", "typ", "objednavka_zmluva_link", "suma", "platobny_prikaz", "splatnost_datum", "dane_na_uhradu", "zdroj", "zakazka", "ekoklas"]
    search_fields = ["^cislo","typ", "objednavka_zmluva__dodavatel__nazov", "^zdroj__kod", "^zakazka__kod", "^ekoklas__kod" ]
    def get_readonly_fields(self, request, obj=None):
        if obj:
            #return ["objednavka_zmluva", "cislo", "splatnost_datum", "typ", "program", "ekoklas", "zakazka", "zdroj", "platobny_prikaz"]
            if obj.platobny_prikaz:
                return ["objednavka_zmluva", "cislo", "splatnost_datum", "typ", "program", "ekoklas", "platobny_prikaz"]
            else:
                return ["objednavka_zmluva", "cislo", "splatnost_datum", "typ", "program", "ekoklas", "platobny_prikaz", "dane_na_uhradu"]
        else:
            return ["dane_na_uhradu", "platobny_prikaz"]

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
    actions = ['vytvorit_platobny_prikaz']

    def vytvorit_platobny_prikaz(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu položku", messages.ERROR)
            return
        platba = queryset[0]
        if platba.dane_na_uhradu:
            self.message_user(request, f"Platba už bola daná na úhradu, vytváranie platobného príkazu nie je možné", messages.ERROR)
            return
        status, msg, vytvoreny_subor = VytvoritPlatobnyPrikaz(platba, request.user)
        if status != messages.ERROR:
            platba.platobny_prikaz = vytvoreny_subor
            platba.save()
        self.message_user(request, msg, status)

    vytvorit_platobny_prikaz.short_description = "Vytvoriť platobný príkaz a krycí list pre THS"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_platobny_prikaz.allowed_permissions = ('change',)

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(PravidelnaPlatbaAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

@admin.register(InternyPrevod)
#medzi  ModelAdminTotals a ImportExportModelAdmin je konflikt
#zobrazia sa Import Export tlačidlá alebo súčty
#class InternyPrevodAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
class InternyPrevodAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = InternyPrevodForm
    list_display = ["cislo", "partner_link", "suma", "predmet", "na_zaklade", "platobny_prikaz", "doslo_datum", "splatnost_datum", "dane_na_uhradu", "zdroj", "zakazka", "ekoklas"]
    search_fields = ["^cislo", "partner__nazov", "^zdroj__kod", "^zakazka__kod", "^ekoklas__kod" ]
    def get_readonly_fields(self, request, obj=None):
        if obj:
            #return ["objednavka_zmluva", "cislo", "splatnost_datum", "typ", "program", "ekoklas", "zakazka", "zdroj", "platobny_prikaz"]
            if obj.platobny_prikaz:
                return ["partner", "cislo", "splatnost_datum", "program", "ekoklas", "platobny_prikaz"]
            else:
                return ["partner", "cislo", "splatnost_datum", "program", "ekoklas", "platobny_prikaz", "dane_na_uhradu"]
        else:
            return ["dane_na_uhradu", "platobny_prikaz"]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    # Vyžaduje, aby ObjednavkaZmluva zmluva bola PolymorphicModel
    change_links = [
        ('partner', {
            'label': "Interný partner",
            'admin_order_field': 'partner__cislo', # Allow to sort members by the `xxx_link` column
        })
    ] 
    list_totals = [
        ('suma', Sum),
    ]
    actions = ['vytvorit_platobny_prikaz']

    def vytvorit_platobny_prikaz(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu položku", messages.ERROR)
            return
        platba = queryset[0]
        if platba.dane_na_uhradu:
            self.message_user(request, f"Platba už bola daná na úhradu, vytváranie platobného príkazu nie je možné", messages.ERROR)
            return
        status, msg, vytvoreny_subor = VytvoritPlatobnyPrikazIP(platba, request.user)
        if status != messages.ERROR:
            platba.platobny_prikaz = vytvoreny_subor
            platba.save()
        self.message_user(request, msg, status)

    vytvorit_platobny_prikaz.short_description = "Vytvoriť platobný príkaz a krycí list pre THS"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_platobny_prikaz.allowed_permissions = ('change',)

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(InternyPrevodAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

@admin.register(Najomnik)
class NajomnikAdmin(ZobrazitZmeny, SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("nazov", "zastupeny", "s_danou", "bankovy_kontakt", "adresa") 
    search_fields = ("nazov", "zastupeny")
    def adresa(self, obj):
        if obj.adresa_mesto:
            return f"{obj.adresa_ulica} {obj.adresa_mesto}, {obj.adresa_stat}".strip()
    adresa.short_description = "Adresa"

@admin.register(NajomnaZmluva)
class NajomnaZmluvaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    form = NajomnaZmluvaForm
    list_display = ("cislo", "orig_cislo", "najomnik_link", "datum_zverejnenia_CRZ", "datum_do", "url_zmluvy_html", "miestnosti", "vymery", "poznamka")
    search_fields = ("najomnik__nazov", "najomnik__zastupeny")

    # formátovať pole url_zmluvy
    def url_zmluvy_html(self, obj):
        if obj.url_zmluvy:
            return format_html(f'<a href="{obj.url_zmluvy}" target="_blank">pdf</a>')
        else:
            return None
    url_zmluvy_html.short_description = "Zmluva v CRZ"

    change_links = [
        ('najomnik', {
            'admin_order_field': 'najomnik__nazov', # Allow to sort members by the column
        })
    ]


    def orig_cislo(self, obj):
        parsed = re.findall(f"{NajomnaZmluva.oznacenie}-(....)-(...)", obj.cislo)
        if parsed:
            rok, nn = parsed[0]
            rok = int(rok)
            nn = int(nn)
        if rok < 2022:
            return "%02d/%d"%(nn, rok)
        else:
            return "-"
    orig_cislo.short_description = "Pôv. číslo"

@admin.register(NajomneFaktura)
class NajomneFakturaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    form = NajomneFakturaForm
    list_display = ("cislo", "cislo_softip", "zmluva_link", "typ", "splatnost_datum", "dane_na_uhradu", "suma", "_dph", "platobny_prikaz")
    def _dph(self, obj):
        if obj.typ != TypPN.NAJOMNE or obj.zmluva.najomnik.s_danou == AnoNie.ANO:
            return round(obj.suma*DPH/100,2)
        else:
            return 0
    #search_fields = ("nazov", "zastupeny")
    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return ["dane_na_uhradu", "cislo_softip", "platobny_prikaz" ]
        else:
            if not obj.cislo_softip:
                #return ["dane_na_uhradu", "platobny_prikaz"]
                return ["platobny_prikaz"]
        return ["platobny_prikaz"]
    actions = ['vytvorit_platobny_prikaz']

    search_fields = ["cislo", "zmluva__cislo", "zmluva__najomnik__nazov"]

    # zoraďovateľný odkaz na dodávateľa
    change_links = [
        ('zmluva', {
            'admin_order_field': 'zmluva__najomnik__nazov', # Allow to sort members by the column
        })
    ]

    def vytvorit_platobny_prikaz(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu položku", messages.ERROR)
            return
        platba = queryset[0]
        if not platba.cislo_softip:
            self.message_user(request, f"Faktúra nemá zadané číslo zo Softipu,  vytváranie platobného príkazu nie je možné", messages.ERROR)
            return
        if platba.suma < 0: #ak platíme (len vyúčtovanie)
            status, msg, vytvoreny_subor = VytvoritPlatobnyPrikaz(platba, request.user)
        else:
            status, msg, vytvoreny_subor = VytvoritKryciList(platba, request.user)
        if status != messages.ERROR:
            platba.platobny_prikaz = vytvoreny_subor
            platba.save()
        self.message_user(request, msg, status)
    vytvorit_platobny_prikaz.short_description = "Vytvoriť krycí list pre THS"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_platobny_prikaz.allowed_permissions = ('change',)

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(NajomneFakturaAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

@admin.register(RozpoctovaPolozka)
class RozpoctovaPolozkaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    list_display = ["cislo", "suma",  "zdroj", "zakazka", "ekoklas", "cinnost" ]
    search_fields = ["cislo", "^zdroj__kod", "^zakazka__kod", "^ekoklas__kod", "^cinnost__kod" ]
    exclude = ["program", "poznamka"]
    list_totals = [
        ('suma', Sum),
    ]
    def get_readonly_fields(self, request, obj=None):
        return [ "cislo", "suma", "ekoklas", "zakazka", "zdroj", "cinnost"]

@admin.register(RozpoctovaPolozkaDotacia)
class RozpoctovaPolozkaDotaciaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = RozpoctovaPolozkaDotaciaForm
    list_display = ["cislo", "suma",  "rozpoctovapolozka_link", "zdroj", "zakazka", "ekoklas", "cinnost" ]
    search_fields = ["cislo", "^zdroj__kod", "rozpoctovapolozka__cislo", "^zakazka__kod", "^ekoklas__kod", "^cinnost__kod" ]
    exclude = ["program", "rozpoctovapolozka"]
    list_totals = [
        ('suma', Sum),
    ]
    def get_readonly_fields(self, request, obj=None):
        return [ "cislo", "suma", "ekoklas", "zakazka", "zdroj", "cinnost"] if obj else []

    # zoraďovateľný odkaz na dodávateľa
    change_links = [
        ('rozpoctovapolozka', {
            'admin_order_field': 'rozpoctovapolozka__cislo', # Allow to sort members by the column
        })
    ]

@admin.register(PrispevokNaStravne)
class PrispevokNaStravneAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = PrispevokNaStravneForm
    list_display = ["cislo", "za_mesiac", "po_zamestnancoch", "suma_zamestnavatel", "suma_socfond"]
    search_fields = ["cislo"]
    # určiť poradie poli v editovacom formulári
    fields = ["cislo", "za_mesiac", "suma_zamestnavatel", "suma_socfond", "po_zamestnancoch", "zdroj", "zakazka", "ekoklas", "cinnost" ]

    list_totals = [
        ('suma_zamestnavatel', Sum),
        ('suma_socfond', Sum),
    ]
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [ "program", "ekoklas", "zakazka", "zdroj", "cinnost"]
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

#Skryť ZamestnanecDohodar, zobrazujeme Zamestnanec a Dohodar
#@admin.register(ZamestnanecDohodar)
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
    list_display = ("priezvisko", "meno", "cislo_zamestnanca", "zamestnanie_od", "zamestnanie_enu_od", "rod_priezvisko", "email", "rodne_cislo", "datum_nar", "miesto_nar", "adresa", "_dochodok", "_ztp","poistovna", "cop", "stav")
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

class DohodaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    #Polia Dohoda: cislo zmluvna_strana stav_dohody dohoda_odoslana vynimka predmet datum_od datum_do vyplatene subor_dohody sken_dohody
    #Polia Klasifikacia: zdroj program zakazka ekoklas 
    # skryť vo formulári na úpravu
    exclude = ["program"]
    def get_list_display(self, request):
        #cislo a zmluvna_strana riešime v odvodenej triede
        return ("stav_dohody", "dohoda_odoslana", "_predmet", "datum_od", "datum_do", "vyplatene", "subor_dohody", "sken_dohody", "vynimka")
    def get_readonly_fields(self, request, obj=None):
        polia_klasif = ["zdroj", "zakazka", "ekoklas"]
        if not obj:
            return ["subor_dohody","sken_dohody", "dohoda_odoslana", "vyplatene"]
        elif obj.stav_dohody == StavDohody.NOVA or obj.stav_dohody == StavDohody.VYTVORENA: 
            return ["cislo", "zmluvna_strana", "subor_dohody","sken_dohody", "dohoda_odoslana", "vyplatene"]
        elif obj.stav_dohody == StavDohody.NAPODPIS: 
            return polia_klasif + ["cislo", "zmluvna_strana", "subor_dohody", "sken_dohody", "predmet", "datum_od", "datum_do", "vynimka", "vyplatene"]
        elif obj.stav_dohody == StavDohody.ODOSLANA_DOHODAROVI: 
            return polia_klasif + ["cislo", "zmluvna_strana", "subor_dohody", "sken_dohody", "dohoda_odoslana", "predmet", "datum_od", "datum_do", "vynimka", "vyplatene"]
        elif obj.stav_dohody == StavDohody.PODPISANA_DOHODAROM:
            return polia_klasif + ["cislo", "zmluvna_strana", "subor_dohody", "dohoda_odoslana", "predmet", "datum_od", "datum_do", "vynimka", "vyplatene"]
        elif obj.stav_dohody == StavDohody.DOKONCENA:
            return polia_klasif + ["cislo", "zmluvna_strana", "subor_dohody", "dohoda_odoslana", "predmet", "datum_od", "datum_do", "vynimka"]
        else:
            #sem by sme nemali prist
            return polia_klasif
            
    def _predmet(self, obj):
        if obj:
            return obj.predmet if len(obj.predmet) < 60 else f"{obj.predmet[:60]}..."
    _predmet.short_description = "Pracovná činnosť                             " # nezalomiteľné medzery ...

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    # Použité v odvodenenej triede
    change_links = [
        ('zmluvna_strana', {
            'admin_order_field': 'zmluvna_strana__priezvisko', # Allow to sort members by the column
        })
    ]

    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["cislo", "zmluvna_strana__priezvisko"]

    actions = ['vytvorit_subor_dohody']
    def vytvorit_subor_dohody(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu dohodu", messages.ERROR)
            return
        dohoda = queryset[0]
        status, msg, vytvoreny_subor = VytvoritSuborDohody(dohoda)
        if status != messages.ERROR:
            dohoda.subor_dohody = vytvoreny_subor
            dohoda.stav_dohody = StavDohody.VYTVORENA
            dohoda.save()
        self.message_user(request, f"Dohodu treba po vytvorení súboru dať na podpis vedeniu EnÚ a jej stav treba zmeniť na '{StavDohody.NAPODPIS.label}'", messages.WARNING)
        self.message_user(request, msg, status)

    vytvorit_subor_dohody.short_description = "Vytvoriť súbor dohody"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_subor_dohody.allowed_permissions = ('change',)

@admin.register(DoVP)
class DoVPAdmin(DohodaAdmin):
    #Polia DoVP: odmena_celkom hod_celkom id_tsh pomocnik
    form = DoVPForm
    def get_list_display(self, request):
        list_display = ("cislo", "zmluvna_strana_link", "odmena_celkom", "hod_celkom", "poznamka" )
        return list_display + super(DoVPAdmin, self).get_list_display(request)
    def get_readonly_fields(self, request, obj=None):
        # polia rodičovskej triedy
        ro_parent = super(DoVPAdmin, self).get_readonly_fields(request, obj)
        if not obj:
            return ro_parent
        elif obj.stav_dohody == StavDohody.NOVA or obj.stav_dohody == StavDohody.VYTVORENA: 
            return ro_parent
        elif obj.stav_dohody == StavDohody.NAPODPIS: 
            return ro_parent + ["odmena_celkom", "hod_celkom", "pomocnik"]
        elif obj.stav_dohody == StavDohody.ODOSLANA_DOHODAROVI: 
            return ro_parent + ["odmena_celkom", "hod_celkom", "pomocnik"]
        elif obj.stav_dohody == StavDohody.PODPISANA_DOHODAROM:
            return ro_parent + ["odmena_celkom", "hod_celkom", "pomocnik"]
        elif obj.stav_dohody == StavDohody.DOKONCENA:
            return ro_parent + ["odmena_celkom", "hod_celkom", "pomocnik"]
        else:
            #sem by sme nemali prist
            trace()
            pass
            return ro_parent

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(DoVPAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

    # od februára 2022 sa id_tsh nepoužíva
    exclude = ["id_tsh"]
    list_totals = [
        ('odmena_celkom', Sum),
    ]

@admin.register(DoBPS)
class DoBPSAdmin(DohodaAdmin):
    #Polia DoBPS: odmena_celkom hod_mesacne datum_ukoncenia
    form = DoBPSForm
    def get_list_display(self, request):
        list_display = ("cislo", "zmluvna_strana_link", "odmena_celkom", "hod_mesacne", "datum_ukoncenia", "poznamka" )
        return list_display + super(DoBPSAdmin, self).get_list_display(request)
    def get_readonly_fields(self, request, obj=None):
        # polia rodičovskej triedy
        ro_parent = super(DoBPSAdmin, self).get_readonly_fields(request, obj)
        if not obj:
            return ro_parent
        elif obj.stav_dohody == StavDohody.NOVA or obj.stav_dohody == StavDohody.VYTVORENA: 
            return ro_parent
        elif obj.stav_dohody == StavDohody.NAPODPIS: 
            return ro_parent + ["odmena_celkom", "hod_mesacne", "datum_ukoncenia"]
        elif obj.stav_dohody == StavDohody.ODOSLANA_DOHODAROVI: 
            return ro_parent + ["odmena_celkom", "hod_mesacne", "datum_ukoncenia"]
        elif obj.stav_dohody == StavDohody.PODPISANA_DOHODAROM:
            return ro_parent + ["odmena_celkom", "hod_mesacne"]
        elif obj.stav_dohody == StavDohody.DOKONCENA:
            return ro_parent + ["odmena_celkom", "hod_mesacne"]
        else:
            #sem by sme nemali prist
            return ro_parent

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(DoBPSAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

    list_totals = [
        ('odmena_celkom', Sum),
    ]

@admin.register(DoPC)
class DoPCAdmin(DohodaAdmin):
#class DoPCAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    #Polia DoPC: odmena_mesacne hod_mesacne datum_ukoncenia
    form = DoPCForm
    #list_display = ("cislo", "zmluvna_strana_link", "stav_dohody", "dohoda_odoslana", "vyplatene", "_predmet", "vynimka", "subor_dohody", "sken_dohody", "odmena_mesacne", "hod_mesacne", "datum_od", "datum_do", "datum_ukoncenia", "poznamka" )
    def get_list_display(self, request):
        list_display = ("cislo", "zmluvna_strana_link", "odmena_mesacne", "hod_mesacne", "datum_ukoncenia", "poznamka" )
        return list_display + super(DoPCAdmin, self).get_list_display(request)
    def get_readonly_fields(self, request, obj=None):
        # polia rodičovskej triedy
        ro_parent = super(DoPCAdmin, self).get_readonly_fields(request, obj)
        if not obj:
            return ro_parent + ["datum_ukoncenia"]
        elif obj.stav_dohody == StavDohody.NOVA or obj.stav_dohody == StavDohody.VYTVORENA: 
            return ro_parent + ["datum_ukoncenia"]
        elif obj.stav_dohody == StavDohody.NAPODPIS: 
            return ro_parent + ["odmena_mesacne", "hod_mesacne", "datum_ukoncenia"]
        elif obj.stav_dohody == StavDohody.ODOSLANA_DOHODAROVI: 
            return ro_parent + ["odmena_mesacne", "hod_mesacne", "datum_ukoncenia"]
        elif obj.stav_dohody == StavDohody.PODPISANA_DOHODAROM:
            return ro_parent + ["odmena_mesacne", "hod_mesacne"]
        elif obj.stav_dohody == StavDohody.DOKONCENA:
            return ro_parent + ["odmena_mesacne", "hod_mesacne"]
        else:
            #sem by sme nemali prist
            return ro_parent

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(DoPCAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

    list_totals = [
        ('odmena_mesacne', Sum),
    ]

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

@admin.register(Nepritomnost)
class NepritomnostAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    form = NepritomnostForm
    list_display = ["cislo", "nepritomnost_od", "nepritomnost_do", "zamestnanec_link", "nepritomnost_typ"]
    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["cislo", "zamestnanec__meno", "zamestnanec__priezvisko", "^nepritomnost_typ"]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('zamestnanec', {
            'admin_order_field': 'zamestnanec__priezvisko', # Allow to sort members by the column
        })
    ]

@admin.register(PlatovyVymer)
class PlatovyVymerAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    form = PlatovyVymerForm
    list_display = ["cislo", "mp","zamestnanec_link", "stav", "zamestnanie_enu_od", "zamestnanie_od", "aktualna_prax", "datum_postup", "_postup_roky", "uvazok", "datum_od", "datum_do", "_zamestnanie_roky_dni", "_top", "_ts", "suborvymer"]
    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["cislo", "zamestnanec__meno", "zamestnanec__priezvisko", "^stav"]
    actions = ['duplikovat_zaznam', export_selected_objects]
    # skryť vo formulári na úpravu
    exclude = ["program"]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('zamestnanec', {
            'admin_order_field': 'zamestnanec__priezvisko', # Allow to sort members by the column
        })
    ]

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.datum_do:
            aux = [f.name for f in PlatovyVymer._meta.get_fields()]
            aux.remove("datum_do")
            return aux
        else:
            return ["zamestnanieroky", "zamestnaniedni", "datum_postup"]

    def zamestnanie_enu_od(self, obj):
        return obj.zamestnanec.zamestnanie_od.strftime('%d. %m. %Y')
    zamestnanie_enu_od.short_description = "1. PP od"

    def zamestnanie_od(self, obj):
        return obj.zamestnanec.zamestnanie_enu_od.strftime('%d. %m. %Y')
    zamestnanie_od.short_description = "PP v EnÚ od"

    def aktualna_prax(self, obj):
        today = date.today()
        prveho =  date(today.year, today.month, 1)
        return vypocet_prax(obj.zamestnanec.zamestnanie_od, prveho-timedelta(1))
    aktualna_prax.short_description = f"Prax k {date(date.today().year, date.today().month, 1).strftime('%d. %m. %Y')}"

    def mp(self, obj):
        if obj.zamestnanec:
            od = obj.datum_od.strftime('%d. %m. %Y') if obj.datum_od else '--'
            return f"{obj.zamestnanec.priezvisko}, {od}".strip()
    mp.short_description = "Výmer"

    def _top(self, obj):
        return f"{obj.tarifny_plat} / {obj.osobny_priplatok} / {obj.funkcny_priplatok}".strip()
    _top.short_description = "Tarifný/osobný/funkčný"

    def _ts(self, obj):
        return f"{obj.platova_trieda} / {obj.platovy_stupen}".strip()
    _ts.short_description = "Trieda/stupeň"

    #zobraziť, po koľký rokoch zamestnania nastane platový postup
    def _postup_roky(self, obj):
        if obj.datum_postup:
            #predchádzajúce roky postupu:
            rp = postup_roky(obj.zamestnanec.zamestnanie_od, obj.datum_postup) 
            if obj.platovy_stupen == 14:
                krok = 0
            else:
                krok = roky_postupu[obj.platovy_stupen] - roky_postupu[obj.platovy_stupen-1] 
            return f"{rp} (krok +{krok})"
        else:
            return "-"
    _postup_roky.short_description = "Postup po rokoch"

    def _zamestnanie_roky_dni(self, obj):
        if obj.datum_do:
            zr, zd = vypocet_zamestnanie(obj.zamestnanec.zamestnanie_enu_od, obj.datum_do)
            return f"{zr}r {zd}d".strip()
        else:
            return "-"
    _zamestnanie_roky_dni.short_description = "PP v EnÚ. k 'Platný do'"

    #ukončí platnosť starého výmeru a aktualizuje prax
    def save_model(self, request, obj, form, change):
        if obj.datum_do:    # ukončený prac. pomer, aktualizovať prax
            years, days = vypocet_zamestnanie(obj.zamestnanec.zamestnanie_enu_od, obj.datum_do)
            obj.zamestnanieroky = years
            obj.zamestnaniedni = days
            obj.datum_postup = None
            obj.stav = StavVymeru.UKONCENY
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
                years, days = vypocet_zamestnanie(obj.zamestnanec.zamestnanie_enu_od, stary.datum_do)
                stary.zamestnanieroky = years
                stary.zamestnaniedni = days
                stary.datum_postup = None
                stary.stav = StavVymeru.NEAKTUALNY
                stary.save()
            dp = datum_postupu( obj.zamestnanec.zamestnanie_od, obj.datum_od + timedelta(30))
            #ak ďalší postu už nie je možný, dp je rovné obj.datum_od. Vtedy ho nezobrazovať 
            obj.datum_postup = dp if dp > obj.datum_od else None
            obj.stav = StavVymeru.AKTUALNY
        super(PlatovyVymerAdmin, self).save_model(request, obj, form, change)

    def duplikovat_zaznam(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jeden výmer.", messages.ERROR)
            return
        star = queryset[0]
        #if star.datum_do:
            #self.message_user(request, f"Tento výmer nie je aktuálny. Duplikovať možno len aktuálny výmer.", messages.ERROR)
            #return
        novy = PlatovyVymer.objects.create(
                cislo_zamestnanca = star.cislo_zamestnanca,
                zamestnanec = star.zamestnanec,
                tarifny_plat = star.tarifny_plat,
                osobny_priplatok = star.osobny_priplatok,
                funkcny_priplatok = star.funkcny_priplatok,
                platova_trieda = star.platova_trieda,
                platovy_stupen = star.platovy_stupen,
                uvazok = star.uvazok,
                program = Program.objects.get(id=4),    #nealokovaný
                ekoklas = star.ekoklas,
                zakazka = star.zakazka,
                zdroj = star.zdroj
            )
        novy.save()
        self.message_user(request, f"Vytvorený bol nový platobný výmer pre {star.zamestnanec}.", messages.SUCCESS)

    duplikovat_zaznam.short_description = "Duplikovať platobný výmer"
    #Oprávnenie na použitie akcie, viazané na 'change'
    duplikovat_zaznam.allowed_permissions = ('change',)


