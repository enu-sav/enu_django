from django.contrib import admin 
from django import forms
from django.utils import timezone
from django.contrib import messages
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models.functions import Collate, Length
from django.db.models import Q
from django.core.exceptions import ValidationError
import re, os
from decimal import Decimal
from datetime import date, datetime, timedelta
from ipdb import set_trace as trace
from .models import EkonomickaKlasifikacia, TypZakazky, Zdroj, Program, Dodavatel, ObjednavkaZmluva
from .models import Objednavka, Zmluva, PrijataFaktura, SystemovySubor, Rozhodnutie, PrispevokNaStravne
from .models import Dohoda, DoVP, DoPC, DoBPS, AnoNie, PlatovyVymer, Vybavovatel
from .models import ZamestnanecDohodar, Zamestnanec, Dohodar, StavDohody, PravidelnaPlatba
from .models import Najomnik, NajomnaZmluva, NajomneFaktura, TypPP, TypPN, Cinnost
from .models import InternyPartner, InternyPrevod, Nepritomnost, RozpoctovaPolozka, RozpoctovaPolozkaDotacia
from .models import RozpoctovaPolozkaPresun, PlatbaBezPrikazu, Pokladna, TypPokladna, SadzbaDPH
from .models import nasledujuce_cislo, nasledujuce_VPD, SocialnyFond, PrispevokNaRekreaciu, OdmenaOprava, OdmenaAleboOprava
from .models import TypNepritomnosti, Stravne, VystavenaFaktura, NakupSUhradou, FormaUhrady, UcetUctovnejOsnovy

from .common import VytvoritPlatobnyPrikaz, VytvoritSuborDohody
from .common import VytvoritKryciList, VytvoritKryciListRekreacia, generovatIndividualneOdmeny, leapdays
from .common import zmazatIndividualneOdmeny, generovatNepritomnost, exportovatNepritomnostUct, VytvoritKryciListOdmena
from .common import VytvoritPlatobnyPrikazIP, VytvoritSuborPD, UlozitStranuPK, TarifnyPlatTabulky

from uctovnictvo import objednavka_actions, nakup_actions, stravne_actions

from .forms import PrijataFakturaForm, AutorskeZmluvyForm, ObjednavkaForm, ZmluvaForm, PrispevokNaStravneForm, PravidelnaPlatbaForm
from .forms import PlatovyVymerForm, NajomneFakturaForm, NajomnaZmluvaForm, PlatbaBezPrikazuForm
from .forms import DoPCForm, DoVPForm, DoBPSForm
from .forms import InternyPrevodForm, NepritomnostForm, RozpoctovaPolozkaDotaciaForm, RozpoctovaPolozkaPresunForm, RozpoctovaPolozkaForm
from .forms import PokladnaForm, SocialnyFondForm, PrispevokNaRekreaciuForm, OdmenaOpravaForm, VystavenaFakturaForm, NakupSUhradouForm 
from .rokydni import datum_postupu, vypocet_prax, vypocet_zamestnanie, postup_roky, roky_postupu
from beliana.settings import DPH, MEDIA_ROOT, MEDIA_URL, UVAZOK_TYZDENNE, DEPLOY_STATE, UCTAREN_NAME
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

# Zoradiť položky v pulldown menu
def formfield_for_foreignkey(instance, db_field, request, **kwargs):
    if db_field.name == "najomnik" and instance.model == NajomnaZmluva:
        kwargs["queryset"] = Najomnik.objects.filter().order_by(Collate('nazov', 'nocase'))
    if db_field.name == "zmluva" and instance.model == NajomneFaktura:
        kwargs["queryset"] = NajomnaZmluva.objects.filter().order_by(Collate('najomnik__nazov', 'nocase'))
    if db_field.name == "dodavatel" and instance.model in [Objednavka, Rozhodnutie, Zmluva]:
        kwargs["queryset"] = Dodavatel.objects.filter().order_by(Collate('nazov', 'nocase'))
    if db_field.name == "objednavka_zmluva" and instance.model in [VystavenaFaktura, PrijataFaktura, PravidelnaPlatba]:
        kwargs["queryset"] = ObjednavkaZmluva.objects.filter().order_by(Collate('dodavatel__nazov', 'nocase'))
    if db_field.name == "zamestnanec" and instance.model in [PlatovyVymer, Nepritomnost, Pokladna, PrispevokNaRekreaciu, OdmenaOprava]:
        kwargs["queryset"] = Zamestnanec.objects.filter().order_by(Collate('priezvisko', 'nocase'))
    if db_field.name == "zmluvna_strana" and instance.model in [DoBPS]:
        kwargs["queryset"] = Dohodar.objects.filter().order_by(Collate('priezvisko', 'nocase'))
    if db_field.name == "zmluvna_strana" and instance.model in [DoVP, DoPC]:
        kwargs["queryset"] = ZamestnanecDohodar.objects.filter().order_by(Collate('priezvisko', 'nocase'))
    if db_field.name == "vybavuje" and instance.model in [NakupSUhradou]:
        kwargs["queryset"] = ZamestnanecDohodar.objects.filter().order_by(Collate('priezvisko', 'nocase'))
    if db_field.name == "ziadatel" and instance.model in [NakupSUhradou]:
        kwargs["queryset"] = ZamestnanecDohodar.objects.filter().order_by(Collate('priezvisko', 'nocase'))
    if db_field.name == "ziadatel" and instance.model in [Objednavka]:
        kwargs["queryset"] = ZamestnanecDohodar.objects.filter().order_by(Collate('priezvisko', 'nocase'))

    if db_field.name == "dodatok_k" and instance.model in [DoPC]:
        kwargs["queryset"] = DoPC.objects.annotate(text_len=Length('cislo')).filter(text_len__lte=15).order_by(Collate('zmluvna_strana__priezvisko', 'nocase'))

    if db_field.name == "zdroj":
        kwargs["queryset"] = Zdroj.objects.filter().order_by('kod')
    if db_field.name == "program":
        kwargs["queryset"] = Program.objects.filter().order_by('kod')
    if db_field.name == "zakazka":
        kwargs["queryset"] = TypZakazky.objects.filter().order_by('kod')
    if db_field.name == "cinnost":
        kwargs["queryset"] = Cinnost.objects.filter().order_by('kod')
    if db_field.name == "ekoklas":
        kwargs["queryset"] = EkonomickaKlasifikacia.objects.filter().order_by('kod')

    if db_field.name == "presun_zdroj":
        kwargs["queryset"] = RozpoctovaPolozka.objects.filter().order_by('-cislo')
    if db_field.name == "presun_ciel":
        kwargs["queryset"] = RozpoctovaPolozka.objects.filter().order_by('-cislo')
    return super(type(instance), instance).formfield_for_foreignkey(db_field, request, **kwargs)

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

@admin.register(UcetUctovnejOsnovy)
class UcetUctovnejOsnovyAdmin(ZobrazitZmeny, SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("kod", "nazov", "kategoria")
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
    list_display = ("cislo", "datum_odoslania", "vybavuje2", "ziadatel", "subor_ziadanky", "subor_objednavky", "subor_prilohy", "predpokladana_cena", "datum_vytvorenia", "termin_dodania", "dodavatel_link","predmet")
    #def formfield_for_dbfield(self, db_field, **kwargs):
        #formfield = super(ObjednavkaAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        #if db_field.name == 'objednane_polozky':
            #formfield.widget = forms.Textarea(attrs=formfield.widget.attrs)
        #return formfield

    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["cislo", "predmet", "dodavatel__nazov"]
    actions = [ 'vytvorit_subor_ziadanky', 'vytvorit_subor_objednavky' ]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('dodavatel', {
            'admin_order_field': 'dodavatel__nazov', # Allow to sort members by the `dodavatel_link` column
        })
    ]

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(ObjednavkaAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

    #obj is None during the object creation, but set to the object being edited during an edit
    def get_readonly_fields(self, request, obj=None):
        readonly = ["subor_ziadanky", "subor_objednavky", "datum_vytvorenia"]
        if obj:
            readonly.append("cislo")
        return readonly

    def vytvorit_subor_objednavky(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu objednavku", messages.ERROR)
            return
        objednavka = queryset[0]
        status, msg, vytvoreny_subor = objednavka_actions.VytvoritSuborObjednavky(objednavka, request.user.username)
        self.message_user(request, format_html(mark_safe(msg)), status)
        if status != messages.ERROR:
            objednavka.subor_objednavky = vytvoreny_subor
            objednavka.save()
            msg = f"Vytvorenú objednávku dajte na podpis a potom pred odoslaním <strong>vyplňte pole 'Dátum odoslania'</strong>. Automaticky sa vytvorí záznam v Denníku prijatej a odoslanej pošty."
            self.message_user(request, format_html(msg), messages.WARNING)

    vytvorit_subor_objednavky.short_description = "Vytvoriť súbor objednavky"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_subor_objednavky.allowed_permissions = ('change',)

    def vytvorit_subor_ziadanky(self, request, queryset):
        #Na úvod chceme vytvoriť žiadanky pre veľa objednávok
        #if len(queryset) != 1:
            #self.message_user(request, f"Vybrať možno len jednu objednavku", messages.ERROR)
            #return
        #objednavka = queryset[0]
        for objednavka in queryset:
            status, msg, vytvoreny_subor = objednavka_actions.VytvoritSuborZiadanky(objednavka, request.user.username)
            self.message_user(request, msg, status)
            if status != messages.ERROR:
                objednavka.subor_ziadanky = vytvoreny_subor
                objednavka.save()
                self.message_user(request, f"Vytvorenú žiadanku dajte na podpis. Po podpise vygenerujte súbor objednávky akciou 'Vytvoriť súbor objednavky'.", messages.WARNING)

    vytvorit_subor_ziadanky.short_description = "Vytvoriť súbor žiadanky"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_subor_ziadanky.allowed_permissions = ('change',)

@admin.register(NakupSUhradou)
#class NakupSUhradouAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
class NakupSUhradouAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = NakupSUhradouForm

    #Členenie formulára na časti
    fields_ziadanka = ["ziadatel", "popis", "cena", "subor_ziadanky", "zamietnute", "datum_ziadanky"]
    fields_ziadost = ['vybavuje', 'forma_uhrady', 'zdroj', 'zakazka', 'subor_ucty', "subor_preplatenie", "datum_vybavenia", "pokladna_vpd", "datum_uhradenia"]
    fieldsets = (
        ('Žiadanka k nákupu', {
            'fields': fields_ziadanka
        }),
        ('Spoločné polia', {
            'fields': ["cislo", "objednane_polozky", "poznamka"]
        }),
        ('Žiadosť o preplatenie', {
            'fields': fields_ziadost
        }),
    )

    list_display = ['cislo'] + fields_ziadanka + ["objednane_polozky"] +fields_ziadost
    actions = [ 'vytvorit_subor_ziadanky', "vytvorit_subor_preplatenie"]
    search_fields = ["^cislo", "^pokladna_vpd", "popis", "forma_uhrady"]
    list_totals = [
        ('cena', Sum),
    ]

    def get_field_classification(self, obj = None):
        automatic_fields = ["subor_ziadanky",  "subor_preplatenie", "pokladna_vpd"]
        fields_ziadost = NakupSUhradouAdmin.fields_ziadost
        fields_ziadanka = NakupSUhradouAdmin.fields_ziadanka
        extra_context = {
                'disabled_fields': [],
                'required_fields':  [],
                'next_fields':  []
            }
        if DEPLOY_STATE == "production" and request.user.is_superuser: 
            return extra_context
        extra_context['disabled_fields'] += automatic_fields

        #Nový formulár
        if not obj:
            extra_context['required_fields'] +=  ["cislo", "ziadatel", "popis", "cena", "objednane_polozky"]
            extra_context['next_fields'] += []
            extra_context['disabled_fields'] += fields_ziadost  
            return extra_context

        #Vyplnený formulár
        if not obj.subor_ziadanky:
            extra_context['required_fields'] +=  ["cislo", "ziadatel", "popis", "cena", "objednane_polozky"]
            extra_context['next_fields'] += ["subor_ziadanky"]
            extra_context['disabled_fields'] += fields_ziadost  
        elif obj.zamietnute == AnoNie.ANO:
            extra_context['required_fields'] +=  []
            extra_context['next_fields'] += []
            extra_context['disabled_fields'] += (fields_ziadost  + fields_ziadanka)
        elif obj.subor_ziadanky and not obj.datum_ziadanky:
            extra_context['required_fields'] +=  ["cislo", "ziadatel", "popis", "cena", "objednane_polozky"]
            extra_context['next_fields'] += ["zamietnute", "datum_ziadanky"]
            extra_context['disabled_fields'] += fields_ziadost  
        elif obj.datum_ziadanky and not obj.subor_preplatenie:
            extra_context['required_fields'] += ['objednane_polozky', 'vybavuje', 'forma_uhrady', 'zdroj', 'zakazka', 'subor_ucty']
            extra_context['next_fields'] += ["subor_preplatenie"]
            extra_context['disabled_fields'] += fields_ziadanka + ['cislo', "datum_vybavenia", "datum_uhradenia"]
        elif obj.subor_preplatenie and not obj.datum_vybavenia:
            extra_context['required_fields'] += ['objednane_polozky', 'vybavuje', 'forma_uhrady', 'zdroj', 'zakazka', 'subor_ucty']
            extra_context['next_fields'] += ['datum_vybavenia']
            extra_context['disabled_fields'] += fields_ziadanka + ['cislo', "datum_uhradenia"]
        elif obj.datum_vybavenia and not obj.datum_uhradenia:
            extra_context['required_fields'] += ["datum_uhradenia"]
            extra_context['next_fields'] += ['datum_uhradenia']
            extra_context['disabled_fields'] += fields_ziadanka + ['cislo', 'objednane_polozky', 'vybavuje', 'forma_uhrady', 'zdroj', 'zakazka', 'subor_ucty', "datum_vybavenia"]
        else:
            extra_context['required_fields'] += []
            extra_context['next_fields'] += ["objednane_polozky"]
            extra_context['disabled_fields'] += fields_ziadanka + fields_ziadost

        return extra_context

    def add_view(self, request, form_url='', extra_context=None):
        self.extra_context = self.get_field_classification()
        return super().add_view(request, form_url, extra_context=self.extra_context)
        #return super().add_view(request, form_url)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        self.extra_context = self.get_field_classification(obj)
        return super().change_view(request, object_id, form_url, extra_context=self.extra_context)
        #return super().change_view(request, object_id, form_url)

    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(NakupSUhradouAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                kwargs['extra_context'] = self.extra_context
                return AdminForm(*args, **kwargs)
        return AdminFormMod

    def vytvorit_subor_ziadanky(self, request, queryset):
        #Na úvod chceme vytvoriť žiadanky pre veľa nákupov
        #if len(queryset) != 1:
            #self.message_user(request, f"Vybrať možno len jeden nákup", messages.ERROR)
            #return
        #nakup = queryset[0]
        for nakup in queryset:
            if nakup.datum_ziadanky:
                self.message_user(request, f"Žiadanka {nakup.cislo} už bola odovzdaná na podpis. Opakované vytváranie jej súboru nie je možné.", messages.ERROR)
                return
            status, msg, vytvoreny_subor = nakup_actions.VytvoritSuborZiadanky(nakup)
            self.message_user(request, msg, status)
            if status != messages.ERROR:
                nakup.subor_ziadanky = vytvoreny_subor
                nakup.save()
                self.message_user(request, f"Vytvorenú žiadanku dajte na podpis žiadateľovi a vedeniu. Nákup možno realizovať až po odsúhlasení a podpise. "
                    f"V prípade zamietnutia zadajte v poli '{NakupSUhradou._meta.get_field('zamietnute').verbose_name}' hodnotu 'Áno'.", messages.WARNING)
                self.message_user(request, f"Podpísanú žiadanku založte do šanonu a založenie potvrďte vyplnením poľa '{NakupSUhradou._meta.get_field('datum_ziadanky').verbose_name}'", messages.WARNING)
    vytvorit_subor_ziadanky.short_description = "Vytvoriť súbor žiadanky"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_subor_ziadanky.allowed_permissions = ('change',)

    def vytvorit_subor_preplatenie(self, request, queryset):
        #Na úvod chceme vytvoriť žiadosti pre veľa nákupov
        #if len(queryset) != 1:
            #self.message_user(request, f"Vybrať možno len jeden nákup", messages.ERROR)
            #return
        #nakup = queryset[0]
        for nakup in queryset:
            if not nakup.datum_ziadanky:
                self.message_user(request, 
                    f"Súbor nebol vytvorený, lebo pole '{NakupSUhradou._meta.get_field('datum_ziadanky').verbose_name}' nie je vyplnené.", 
                    messages.ERROR)
                return
            if not nakup.vybavuje:
                self.message_user(request, f"Súbor nebol vytvorený, lebo pole '{NakupSUhradou._meta.get_field('vybavuje').verbose_name}' nie je vyplnené.", messages.ERROR)
                return
            if not nakup.zdroj:
                self.message_user(request, f"Súbor nebol vytvorený, lebo pole '{NakupSUhradou._meta.get_field('zdroj').verbose_name}' nie je vyplnené.", messages.ERROR)
                return
            if not nakup.zdroj:
                self.message_user(request, f"Súbor nebol vytvorený, lebo pole '{NakupSUhradou._meta.get_field('zdroj').verbose_name}' nie je vyplnené.", messages.ERROR)
                return
            if not nakup.zakazka:
                self.message_user(request, f"Súbor nebol vytvorený, lebo pole '{NakupSUhradou._meta.get_field('zakazka').verbose_name}' nie je vyplnené.", messages.ERROR)
                return
            if not nakup.subor_ucty:
                self.message_user(request, f"Súbor nebol vytvorený, lebo pole '{NakupSUhradou._meta.get_field('subor_ucty').verbose_name}' nie je vyplnené.", messages.ERROR)
                return
            if nakup.datum_vybavenia:
                self.message_user(request, f"Žiadosť o preplatenie {nakup.cislo} už bola daná na vybavenie. Opakované vytváranie jej súboru nie je možné.", messages.ERROR)
                return
            status, msg, vytvoreny_subor = nakup_actions.VytvoritSuborPreplatenie(nakup)
            self.message_user(request, msg, status)
            if status != messages.ERROR:
                nakup.subor_preplatenie = vytvoreny_subor
                nakup.save()
                t_datum_vybavenia = NakupSUhradou._meta.get_field('datum_vybavenia').verbose_name
                if nakup.forma_uhrady == FormaUhrady.UCET:
                    self.message_user(request, f"Vytvorenú žiadosť o preplatenie dajte na podpis a potom ju odovzdajte do pošty. Následne vyplňte pole '{t_datum_vybavenia}'.", messages.WARNING)
                else:
                    self.message_user(request, f"Vytvorenú žiadosť o preplatenie dajte na podpis a vyplňte pole '{t_datum_vybavenia}'. Vytvorí sa záznam pokladne", messages.WARNING)
                #t_objednane_polozky = NakupSUhradou._meta.get_field('objednane_polozky').verbose_name
                #t_datum_uhradenia = NakupSUhradou._meta.get_field('datum_uhradenia').verbose_name
    vytvorit_subor_preplatenie.short_description = "Vytvoriť súbor žiadosti o preplatenie"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_subor_preplatenie.allowed_permissions = ('change',)

    #Prenos položiek z Pokladna a PlatbaBezPrikazuForm. Akcia na jednorazové použitie po zavedení triedy NakupSUhradou 
    def prenos(self, request, queryset):
        def prenos_pok(year,item):
            nakup = NakupSUhradou(
                cislo = nasledujuce_cislo(NakupSUhradou, rok=year),
                pokladna_vpd = item.cislo,
                cena = item.suma,
                vybavuje = item.zamestnanec,
                popis = item.popis,
                zdroj = item.zdroj,
                zakazka = item.zakazka,
                objednane_polozky = f"{item.popis} / {item.suma} / - /{item.ekoklas.kod}",
                forma_uhrady = FormaUhrady.HOTOVOST,
                datum_vybavenia = item.datum_transakcie,
                subor_ucty = item.subor_doklad if item.subor_doklad else None,
                poznamka = f"Údaje prenesené z {item.cislo}"
                )
            nakup.save()
            item.ziadanka = nakup
            item.save()
            pass
        def prenos_bez(year,item):
            popis = "Neurčené"
            if "-" in item.predmet:
                popis = item.predmet.split("-")[1]
            elif item.poznamka:
                popis = item.poznamka   #
            ma_ucet = ["PbP-2024-011", "PbP-2024-010", "PbP-2024-009", "PbP-2024-008", "PbP-2024-007", "PbP-2024-006", "PbP-2024-005"]

            nakup = NakupSUhradou(
                cislo = nasledujuce_cislo(NakupSUhradou, rok=year),
                cena = item.suma,
                vybavuje = ZamestnanecDohodar.objects.get(priezvisko="Beniaková"),
                popis = popis,
                zdroj = item.zdroj,
                zakazka = item.zakazka,
                objednane_polozky = f"{popis} / {item.suma} / - /{item.ekoklas.kod}",
                forma_uhrady = FormaUhrady.UCET,
                datum_vybavenia = item.datum_platby,
                subor_ziadanky = item.subor if item.subor else None,
                subor_ucty = item.subor if item.cislo in ma_ucet else None,
                poznamka = f"Údaje prenesené z PlatbaBezPrikazu"
                )
            nakup.save()
            pass
        pqs = Pokladna.objects.filter(typ_transakcie=TypPokladna.VPD)
        bqs = PlatbaBezPrikazu.objects.filter(predmet__startswith="Žiadanka")
        items = []
        for item in pqs:
            items.append([item.datum_transakcie, item])
            #break
        for item in bqs:
            items.append([item.datum_platby, item])
            #break
        items = sorted(items, key=lambda x: x[0])
        for item in items:
            if type(item[1]) == Pokladna: 
                prenos_pok(item[0].year, item[1])
            else:
                prenos_bez(item[0].year, item[1])
    prenos.short_description = "prenos"

@admin.register(Rozhodnutie)
class RozhodnutieAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("cislo", "predmet", "dodavatel_link", "datum_vydania", "poznamka" )

    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["cislo", "dodavatel__nazov"]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('dodavatel', {
            'admin_order_field': 'dodavatel__nazov', # Allow to sort members by the `dodavatel_link` column
        })
    ]
    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)


@admin.register(PlatbaBezPrikazu)
class PlatbaBezPrikazuAdmin(ZobrazitZmeny, SimpleHistoryAdmin, ImportExportModelAdmin):
    form = PlatbaBezPrikazuForm
    list_display = ["cislo", "suma", "predmet", "datum_platby", "subor", "zdroj", "zakazka", "ekoklas"]
    search_fields = ["cislo", "predmet", "zdroj__kod", "zakazka__kod", "ekoklas__kod"]
    exclude = ["program"]
    actions = ['duplikovat_zaznam']

    def duplikovat_zaznam(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu položku", messages.ERROR)
            return
        stara = queryset[0]
        nc = nasledujuce_cislo(PlatbaBezPrikazu)
        nova_platba = PlatbaBezPrikazu.objects.create(
                cislo = nc,
                program = Program.objects.get(id=4),    #nealokovaný
                ekoklas = stara.ekoklas,
                zakazka = stara.zakazka,
                zdroj = stara.zdroj,
                cinnost = stara.cinnost,
                predmet = stara.predmet,
                ucet = stara.ucet,
            )
        nova_platba.save()
        self.message_user(request, f"Vytvorená bola nová platba číslo '{nc}', aktualizujte polia", messages.SUCCESS)

    duplikovat_zaznam.short_description = "Duplikovať platbu"
    #Oprávnenie na použitie akcie, viazané na 'change'
    duplikovat_zaznam.allowed_permissions = ('change',)

    def __save_model(self, request, obj, form, change): #Dočasne vyradené, do vyriešenia automatického plnenia obsahu SocialnyFond
        if 'suma' in form.changed_data:
            if obj.suma >= 0:
                messages.add_message(request, messages.WARNING, "Do poľa 'Suma' sa obvykle vkladajú výdavky (záporná suma), vložili ste však 0 alebo kladnú hodnotu sumy. <br />Ak ide o omyl, hodnotu opravte.") 

        #Ak ide o Prídel do sociálneho fondu - 637016 - vytvoriť položku SF
        if obj.ekoklas == EkonomickaKlasifikacia.objects.get(kod="637016"):
            qs = PlatbaBezPrikazu.objects.filter(cislo = obj.cislo)
            if not qs:
                sf = SocialnyFond(
                    cislo = nasledujuce_cislo(SocialnyFond),
                    suma = -obj.suma,
                    datum_platby = obj.datum_platby,
                    predmet = f"{obj.cislo} - {obj.predmet}"
                )
                sf.save()
                messages.warning(request, 
                    format_html(
                        'Pridaná bola položka sociálneho fondu č. <em>{}</em>.',
                        mark_safe(f'<a href="/admin/uctovnictvo/socialnyfond/{sf.id}/change/">{sf.cislo}</a>'),
                        )
                )
            else:
                qs = SocialnyFond.objects.filter(predmet__startswith = obj.cislo)
                messages.warning(request, 
                    format_html(
                        'Ak treba, upravte aj položku Sociálneho fondu č. <em>{}</em>.',
                        mark_safe(f'<a href="/admin/uctovnictvo/socialnyfond/{qs[0].id}/change/">{qs[0].cislo}</a>'),
                        )
                )

        super(PlatbaBezPrikazuAdmin, self).save_model(request, obj, form, change)

@admin.register(Pokladna)
class PokladnaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = PokladnaForm
    list_display = ["cislo", "typ_transakcie", "cislo_VPD", "suma", "zamestnanec", "ziadanka", "subor_vpd", "datum_transakcie", "datum_softip", "popis"] 
    search_fields = ["cislo", "typ_transakcie","ziadanka__cislo"]
    #actions = [export_selected_objects]
    actions = ['vytvorit_vpd', 'generovat_stranu_PD', 'duplikovat_zaznam']

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('dodavatel', {
            'admin_order_field': 'dodavatel__nazov', # Allow to sort members by the `dodavatel_link` column
        })
    ]
    list_totals = [
        ('suma', Sum),
    ]

    def get_readonly_fields(self, request, obj=None):
        #quick hack: superuser môže kvôli oprave editovať pole datum_softip
        #nejako podobne implementovať aj pre iné triedy, možno pridať permissions "fix_stuff"
        return [] if request.user.has_perm('uctovnictvo.delete_pokladna') else ["datum_softip"]

    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(PokladnaAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

    def duplikovat_zaznam(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jeden výmer.", messages.ERROR)
            return
        star = queryset[0]
        novy = Pokladna.objects.create(
                cislo = nasledujuce_cislo(Pokladna),
                typ_transakcie = star.typ_transakcie,
                zamestnanec = star.zamestnanec,
                popis = star.popis,
                zdroj = star.zdroj,
                zakazka = star.zakazka,
                ekoklas = star.ekoklas,
                cinnost = star.cinnost
            )
        novy.save()
        self.message_user(request, f"Vytvorený bol nový záznam pokladne.", messages.SUCCESS)

    duplikovat_zaznam.short_description = "Duplikovať záznam pokladne"
    #Oprávnenie na použitie akcie, viazané na 'change'
    duplikovat_zaznam.allowed_permissions = ('change',)

    #generuje prehľad pre ths, queryset je ignorované
    def generovat_stranu_PD(self, request, queryset):
        # všetky záznamy, na zistenie počtu už vytvorených strán
        qs = Pokladna.objects.filter().order_by("datum_transakcie")
        if not qs:
            self.message_user(request, f"Žiadne položky na zaznamenanie do PK neboli nájdené.", messages.INFO)
            return
        datumy = set()
        for item in qs:
            if item.datum_softip:
                datumy.add(item.datum_softip)
        strana = len(datumy) + 1

        qs = queryset.filter(datum_softip__isnull=True).order_by("datum_transakcie")
        if not qs:
            self.message_user(request, f"Žiadne nové položky na zaznamenanie do PK neboli nájdené.", messages.INFO)
            return
        status, msg, media_url = UlozitStranuPK(request, qs, strana)
        if status ==  messages.ERROR:
            self.message_user(request, msg, status)
            return

        self.message_user(request, msg, messages.WARNING)
        self.message_user(request, f"Odkaz na vytvorený súbor je trvalo dostupný v denníku prijatej a odoslanej pošty. Počet exportovaných položiek: {len(qs)}", messages.INFO)

        vec = f"Strana pokladničnej knihy"
        cislo_posta = nasledujuce_cislo(Dokument)
        dok = Dokument(
            cislo = cislo_posta,
            cislopolozky = "-",
            datumvytvorenia = date.today(),
            typdokumentu = TypDokumentu.POKLADNICNAKNIHA,
            inout = InOut.ODOSLANY,
            adresat = UCTAREN_NAME,
            vec = f'<a href="{media_url}">{vec}</a>',
            prijalodoslal=request.user.username, #zámena mien prijalodoslal - zaznamvytvoril
        )
        dok.save()
        messages.warning(request, 
            format_html(
                'Do denníka prijatej a odoslanej pošty bol pridaný záznam č. {}: <em>{}</em>, treba v ňom doplniť údaje o odoslaní.',
                mark_safe(f'<a href="/admin/dennik/dokument/{dok.id}/change/">{cislo_posta}</a>'),
                "Pokladničná kniha"
                )
        )
        dnes = date.today()
        for item in qs:
            item.datum_softip = dnes 
            item.save()

    generovat_stranu_PD.short_description = "Vytvoriť stranu pokladničnej knihy"
    #Oprávnenie na použitie akcie, viazané na 'change'
    generovat_stranu_PD.allowed_permissions = ('change',)

    def vytvorit_vpd(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu položku", messages.ERROR)
            return
        vpd = queryset[0]
        if vpd.typ_transakcie == TypPokladna.DOTACIA:
            self.message_user(request, f"Vybraná položka je dotácia, pokladničný doklad nemožno vytvoriť.", messages.ERROR)
            return
        status, msg, vytvoreny_subor = VytvoritSuborPD(vpd)
        if status != messages.ERROR:
            vpd.subor_vpd = vytvoreny_subor
            vpd.save()
        self.message_user(request, msg, status)

    vytvorit_vpd.short_description = "Vytvoriť PD"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_vpd.allowed_permissions = ('change',)

@admin.register(Zmluva)
class ZmluvaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    form = ZmluvaForm
    list_display = ["cislo", "nase_cislo", "dodavatel_link", "predmet", "datum_zverejnenia_CRZ", "trvala_zmluva", "platna_do", "url_zmluvy_html"]
    search_fields = ["dodavatel__nazov", "cislo", "predmet"]
    actions = [export_selected_objects]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('dodavatel', {
            'admin_order_field': 'dodavatel__nazov', # Allow to sort members by the `dodavatel_link` column
        })
    ]

    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

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
class PrijataFakturaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
#class PrijataFakturaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = PrijataFakturaForm
    list_display = ["cislo", "dcislo", "objednavka_zmluva_link", "url_faktury", "url_dodaci", "suma", "sadzbadph", "prenosDP", "zrusena", "podiel2", "predmet", "platobny_prikaz", "dane_na_uhradu", "uhradene_dna", "mena", "zdroj", "zakazka", "zdroj2", "zakazka2", "ucet", "ekoklas"]
    search_fields = ["^cislo", "^dcislo", "^objednavka_zmluva__dodavatel__nazov", "objednavka_zmluva__cislo", "predmet", "^zdroj__kod", "^zakazka__kod", "^ekoklas__kod", "^ekoklas__nazov", "ucet__kod","^cinnost__kod", "cinnost__nazov" ]

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
    actions = ['vytvorit_platobny_prikaz', 'duplikovat_zaznam', "fix_dph"]

    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

    # formátovať pole url_zmluvy
    def url_faktury(self, obj):
        #trace()
        if obj.prijata_faktura:
            suffix = obj.prijata_faktura.name.split(".")[-1]        
            ddir = obj.prijata_faktura.name.split("/")[0]        
            return format_html(f'<a href="{obj.prijata_faktura.url}" target="_blank">{ddir}/***.{suffix}</a>')
        else:
            return None
    url_faktury.short_description = "Faktúra"

    # formátovať pole url_dodaci
    def url_dodaci(self, obj):
        #trace()
        if obj.dodaci_list:
            suffix = obj.dodaci_list.name.split(".")[-1]        
            ddir = obj.dodaci_list.name.split("/")[0]
            return format_html(f'<a href="{obj.dodaci_list.url}" target="_blank">{ddir}/***.{suffix}</a>')
        else:
            return None
    url_dodaci.short_description = "Dodací list"

    #obj is None during the object creation, but set to the object being edited during an edit
    #"platobny_prikaz" je generovaný, preto je vždy readonly
    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return ["program", "platobny_prikaz", "dane_na_uhradu", "uhradene_dna"]
        elif not obj.platobny_prikaz:   #ešte nebola spustená akcia
            return ["program", "cislo", "platobny_prikaz", "dane_na_uhradu", "uhradene_dna"]
        elif obj.dane_na_uhradu:
            nearly_all = ["program", "doslo_datum"] 
            nearly_all += ["splatnost_datum", "mena", "dane_na_uhradu"]
            return nearly_all
        else:   #všetko hotové, možno odoslať, ale stále možno aj editovať
            return ["program", "cislo"]

    #temporary hepler
    def fix_dph(self, request, queryset):
        for faktura in queryset:
            faktura.sadzbadph = SadzbaDPH.P20
            faktura.save()

    fix_dph.short_description = "Fix DPH"
    #Oprávnenie na použitie akcie, viazané na 'change'
    #fix_dph.allowed_permissions = ('change',)


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

    vytvorit_platobny_prikaz.short_description = "Vytvoriť platobný príkaz a krycí list"
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
                zakazka2 = stara.zakazka2,
                zdroj2 = stara.zdroj2,
                podiel2 = stara.podiel2,
                cinnost = stara.cinnost,
                predmet = stara.predmet,
                prenosDP = stara.prenosDP,
                sadzbadph = stara.sadzbadph
            )
        if type(stara.objednavka_zmluva) in [Zmluva, Rozhodnutie]:
            nova_faktura.objednavka_zmluva = stara.objednavka_zmluva
        nova_faktura.save()
        self.message_user(request, f"Vytvorená bola nová faktúra dodávateľa '{stara.objednavka_zmluva.dodavatel.nazov}' číslo '{nc}', aktualizujte polia", messages.SUCCESS)
        vec = f"Faktúra {nc}"
        cislo_posta = nasledujuce_cislo(Dokument)
        dok = Dokument(
            cislo = cislo_posta,
            cislopolozky = nc,
            datumvytvorenia = date.today(),
            typdokumentu = TypDokumentu.FAKTURA,
            inout = InOut.PRIJATY,
            adresat = stara.adresat_text(),
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
                adresat = obj.adresat_text(),
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
                messages.add_message(request, messages.WARNING, "Do poľa 'Suma' sa obvykle vkladajú výdavky (záporná suma), vložili ste však 0 alebo kladnú hodnotu sumy. Ak ide o omyl, hodnotu opravte. Ak ide o platbu v cudzej mene, pole vyplňte dotatočne.") 
        super(PrijataFakturaAdmin, self).save_model(request, obj, form, change)

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(PrijataFakturaAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

@admin.register(VystavenaFaktura)
#medzi  ModelAdminTotals a ImportExportModelAdmin je konflikt
#zobrazia sa Import Export tlačidlá alebo súčty
#class VystavenaFakturaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
class VystavenaFakturaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = VystavenaFakturaForm
    list_display = ["cislo", "objednavka_zmluva_link", "url_faktury", "dcislo", "url_softip", "suma", "sadzbadph", "predmet", "platobny_prikaz", "dane_na_uhradu", "uhradene_dna", "zdroj", "zakazka", "ekoklas"]
    search_fields = ["^cislo","^dcislo", "objednavka_zmluva__dodavatel__nazov", "predmet", "^zdroj__kod", "^zakazka__kod", "^ekoklas__kod", "^ekoklas__nazov",  "^cinnost__kod", "cinnost__nazov" ]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    # Vyžaduje, aby ObjednavkaZmluva zmluva bola PolymorphicModel
    change_links = [
        ('objednavka_zmluva', {
            'label': "Zmluva",
            'admin_order_field': 'objednavka_zmluva__cislo', # Allow to sort members by the `xxx_link` column
        })
    ] 
    list_totals = [
        ('suma', Sum),
    ]
    actions = ['vytvorit_platobny_prikaz', 'duplikovat_zaznam']

    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

    # formátovať pole url_zmluvy
    def url_faktury(self, obj):
        #trace()
        if obj.na_zaklade:
            suffix = obj.na_zaklade.name.split(".")[-1]        
            fname = obj.na_zaklade.name.split("/")[-1].split(".")[-2][:7]
            ddir = obj.na_zaklade.name.split("/")[0]        
            return format_html(f'<a href="{obj.na_zaklade.url}" target="_blank">VF/{fname}***.{suffix}</a>')
        else:
            return None
    url_faktury.short_description = "Na základe"

    # formátovať pole zo_softipu
    def url_softip(self, obj):
        if obj.na_zaklade:
            suffix = obj.zo_softipu.name.split(".")[-1]        
            fname = obj.zo_softipu.name.split("/")[-1].split(".")[-2][:7]
            ddir = obj.zo_softipu.name.split("/")[0]        
            return format_html(f'<a href="{obj.zo_softipu.url}" target="_blank">VF/{fname}***.{suffix}</a>')
        else:
            return None
    url_softip.short_description = "Zo Softipu"

    #obj is None during the object creation, but set to the object being edited during an edit
    #"platobny_prikaz" je generovaný, preto je vždy readonly
    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return ["program", "platobny_prikaz", "dane_na_uhradu", "uhradene_dna"]
        elif not obj.platobny_prikaz:   #ešte nebola spustená akcia
            return ["program", "cislo", "platobny_prikaz", "dane_na_uhradu", "uhradene_dna"]
        elif obj.dane_na_uhradu:
            nearly_all = ["program", "doslo_datum"] 
            nearly_all += ["splatnost_datum", "dane_na_uhradu"]
            return nearly_all
        else:   #všetko hotové, možno odoslať, ale stále možno aj editovať
            return ["program", "cislo"]

    def vytvorit_platobny_prikaz(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu položku", messages.ERROR)
            return
        faktura = queryset[0]
        if faktura.dane_na_uhradu:
            self.message_user(request, f"Faktúra už bola daná na úhradu, vytváranie krycieho listu nie je možné", messages.ERROR)
            return
        status, msg, vytvoreny_subor = VytvoritKryciList(faktura, request.user)
        if status != messages.ERROR:
            #faktura.dane_na_uhradu = timezone.now()
            faktura.platobny_prikaz = vytvoreny_subor
            faktura.save()
        self.message_user(request, msg, status)

    vytvorit_platobny_prikaz.short_description = "Vytvoriť krycí list"
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
        nc = nasledujuce_cislo(VystavenaFaktura)
        nova_faktura = VystavenaFaktura.objects.create(
                cislo = nc,
                program = Program.objects.get(id=4),    #nealokovaný
                ekoklas = stara.ekoklas,
                zakazka = stara.zakazka,
                zdroj = stara.zdroj,
                zakazka2 = stara.zakazka2,
                zdroj2 = stara.zdroj2,
                podiel2 = stara.podiel2,
                cinnost = stara.cinnost,
                predmet = stara.predmet,
                sadzbadph = stara.sadzbadph,
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
            typdokumentu = TypDokumentu.VYSTAVENAFAKTURA,
            inout = InOut.PRIJATY,
            adresat = stara.adresat_text(),
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
        if not VystavenaFaktura.objects.filter(cislo=obj.cislo):  #Faktúra ešte nie je v databáze
            vec = f"Vystavená faktúra {obj.cislo}"
            cislo_posta = nasledujuce_cislo(Dokument)
            dok = Dokument(
                cislo = cislo_posta,
                cislopolozky = obj.cislo,
                #datumvytvorenia = self.cleaned_data['doslo_datum'],
                datumvytvorenia = date.today(),
                typdokumentu = TypDokumentu.VYSTAVENAFAKTURA,
                inout = InOut.PRIJATY,
                adresat = obj.adresat_text(),
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
        super(VystavenaFakturaAdmin, self).save_model(request, obj, form, change)

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(VystavenaFakturaAdmin, self).get_form(request, obj, **kwargs)
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
    list_display = ["cislo", "typ", "objednavka_zmluva_link", "suma", "platobny_prikaz", "splatnost_datum", "dane_na_uhradu", "uhradene_dna", "zdroj", "zakazka", "ucet", "ekoklas"]
    search_fields = ["^cislo","typ", "objednavka_zmluva__dodavatel__nazov", "^zdroj__kod", "^zakazka__kod", "ucet__kod", "^ekoklas__kod" ]
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

    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

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

    vytvorit_platobny_prikaz.short_description = "Vytvoriť platobný príkaz a krycí list"
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
    list_display = ["cislo", "partner_link", "suma", "predmet", "na_zaklade", "platobny_prikaz", "doslo_datum", "splatnost_datum", "dane_na_uhradu", "uhradene_dna", "zdroj", "zakazka", "ucet", "ekoklas"]
    search_fields = ["^cislo", "partner__nazov", "^zdroj__kod", "^zakazka__kod", "ucet__kod", "^ekoklas__kod" ]
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

    vytvorit_platobny_prikaz.short_description = "Vytvoriť platobný príkaz a krycí list"
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
    list_display = ("nazov", "zastupeny", "bankovy_kontakt", "adresa") 
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

    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

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
        rok = None
        if parsed:
            rok, nn = parsed[0]
            rok = int(rok)
            nn = int(nn)
        if rok and rok < 2022:
            return "%02d/%d"%(nn, rok)
        else:
            return "-"
    orig_cislo.short_description = "Pôv. číslo"

@admin.register(NajomneFaktura)
class NajomneFakturaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    form = NajomneFakturaForm
    list_display = ("cislo", "cislo_softip", "zo_softipu", "zmluva_link", "typ", "splatnost_datum", "dane_na_uhradu", "uhradene_dna", "suma", "dan", "zakazka", "ucet", "ekoklas", "platobny_prikaz")

    #Vyhľadávanie podľa 'typ' nefunguje
    search_fields = ("zmluva", "^zakazka", "^ekoklas")
    #search_fields = ("zmluva", "typ")
    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return ["dane_na_uhradu", "platobny_prikaz" ]
        else:
            if not obj.cislo_softip:
                #return ["dane_na_uhradu", "platobny_prikaz"]
                return ["platobny_prikaz"]
        return ["platobny_prikaz"]

    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

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
    vytvorit_platobny_prikaz.short_description = "Vytvoriť krycí list"
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
    form = RozpoctovaPolozkaForm
    list_display = ["cislo", "suma",  "za_rok", "zdroj", "zakazka", "ekoklas", "cinnost" ]
    search_fields = ["cislo", "za_rok", "^zdroj__kod", "^zakazka__kod", "^ekoklas__kod", "^cinnost__kod" ]
    exclude = ["program", "poznamka"]
    list_totals = [
        ('suma', Sum),
    ]
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["cislo", "suma", "ekoklas", "zakazka", "zdroj", "cinnost", "za_rok"]
        else:
            return ["suma"]

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(RozpoctovaPolozkaAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

@admin.register(RozpoctovaPolozkaDotacia)
class RozpoctovaPolozkaDotaciaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = RozpoctovaPolozkaDotaciaForm
    list_display = ["cislo", "suma", "za_rok",  "rozpoctovapolozka_link", "poznamka", "zdroj", "zakazka", "ekoklas"]
    search_fields = ["cislo", "za_rok", "^zdroj__kod", "rozpoctovapolozka__cislo", "^zakazka__kod", "^ekoklas__kod", "^cinnost__kod" ]
    exclude = ["program", "rozpoctovapolozka"]
    list_totals = [
        ('suma', Sum),
    ]
    def get_readonly_fields(self, request, obj=None):
        return [ "cislo", "za_rok", "suma", "ekoklas", "zakazka", "zdroj", "cinnost"] if obj else []

    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(RozpoctovaPolozkaDotaciaAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

    def delete_queryset(self, request, queryset):
        for qq in queryset:
            qq.rozpoctovapolozka.suma -= qq.suma
            qq.rozpoctovapolozka.save()
            qq.delete()

    # zoraďovateľný odkaz na polozku
    change_links = [
        ('rozpoctovapolozka', {
            'admin_order_field': 'rozpoctovapolozka__cislo', # Allow to sort members by the column
        })
    ]

@admin.register(RozpoctovaPolozkaPresun)
class RozpoctovaPolozkaPresunAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = RozpoctovaPolozkaPresunForm
    list_display = ["cislo", "suma",  "presun_zdroj_link", "presun_ciel_link", "dovod"]
    search_fields = ["cislo", "presun_zdroj__cislo", "presun_ciel__cislo", "dovod"]
    list_totals = [
        ('suma', Sum),
    ]
    def get_readonly_fields(self, request, obj=None):
        return [ "cislo", "suma", "presun_zdroj", "presun_ciel"] if obj else []

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

    # pri odstraňovaní napraviť aj dothnuté položky 
    def delete_queryset(self, request, queryset):
        for qq in queryset:
            qq.presun_zdroj.suma += qq.suma
            qq.presun_ciel.suma -= qq.suma
            qq.presun_zdroj.save()
            qq.presun_ciel.save()
            qq.delete()

    # zoraďovateľný odkaz na dodávateľa
    change_links = [
        ('presun_zdroj', {
            'admin_order_field': 'presun_zdroj__cislo', # Allow to sort members by the column
        }),
        ('presun_ciel', {
            'admin_order_field': 'presun_ciel__cislo', # Allow to sort members by the column
        })
    ]

@admin.register(PrispevokNaStravne)
class PrispevokNaStravneAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = PrispevokNaStravneForm
    list_display = ["cislo", "typ_zoznamu", "za_mesiac", "datum_odoslania", "po_zamestnancoch", "suma_zamestnavatel", "zrazka_zamestnavatel", "suma_socfond", "zrazka_socfond"]
    search_fields = ["cislo","^typ_zoznamu", "^za_mesiac"]
    # určiť poradie poli v editovacom formulári
    fields = ["cislo", "typ_zoznamu", "za_mesiac", "datum_odoslania", "suma_zamestnavatel", "zrazka_zamestnavatel", "suma_socfond", "zrazka_socfond", "po_zamestnancoch", "zdroj", "zakazka", "ekoklas", "cinnost" ]

    def _zrazka_spolu(self, obj):
        return obj.zrazka_zamestnavatel + obj.zrazka_socfond
    _zrazka_spolu.short_description = "Zrážky spolu"

    def _suma_spolu(self, obj):
        return obj.suma_zamestnavatel + obj.suma_socfond
    _suma_spolu.short_description = "Prísp.spolu"

    list_totals = [
        ('suma_zamestnavatel', Sum),
        ('suma_socfond', Sum),
        ('zrazka_zamestnavatel', Sum),
        ('zrazka_socfond', Sum),
    ]
    def get_readonly_fields(self, request, obj=None):
        if DEPLOY_STATE == "production" and request.user.is_superuser: return []
        fields = [f.name for f in PrispevokNaStravne._meta.get_fields()]
        to_remove = ["datum_odoslania", "cislo", "za_mesiac", "program", "ekoklas", "zakazka", "zdroj", "cinnost"]
        for tr in to_remove:
            fields.remove(tr)
        return fields

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(PrispevokNaStravneAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

    actions = ['generovat_prispevky_zrazky']

    def __save_model(self, request, obj, form, change): #Dočasne vyradené, do vyriešenia automatického plnenia obsahu SocialnyFond
        #Ak ide o novú platbu, vytvoriť položku SF
        qs = PrispevokNaStravne.objects.filter(cislo = obj.cislo)
        if not qs:
            sf = SocialnyFond(
                cislo = nasledujuce_cislo(SocialnyFond),
                suma = obj.suma_socfond,
                datum_platby = date.today(),
                predmet = f'{obj.cislo} - {"príspevok na stravné" if obj.suma_socfond < 0 else "preplatok za stravné"} za {obj.za_mesiac}'
            )
            sf.save()
            messages.warning(request, 
                format_html(
                    'Pridaná bola položka sociálneho fondu č. <em>{}</em>.',
                    mark_safe(f'<a href="/admin/uctovnictvo/socialnyfond/{sf.id}/change/">{sf.cislo}</a>'),
                    )
            )
        else:
            qs = SocialnyFond.objects.filter(predmet__startswith = obj.cislo)
            messages.warning(request, 
                format_html(
                    'Ak treba, upravte aj položku Sociálneho fondu č. <em>{}</em>.',
                    mark_safe(f'<a href="/admin/uctovnictvo/socialnyfond/{qs[0].id}/change/">{qs[0].cislo}</a>'),
                    )
            )

        super(PrispevokNaStravneAdmin, self).save_model(request, obj, form, change)

    # Vygeneruje príspevky na stravné za EnÚ aj SF za nasledujúci nevyplnený mesiac
    def generovat_prispevky_zrazky(self, request, queryset):
        if len(queryset) != 1:
            messages.error(request, "Vybrať možno len jednu položku")
            return
        obj = queryset[0]
        rslt = stravne_actions.generovatStravne(obj)
        if len(rslt) == 1:  #Chyba
            messages.error(request, rslt[0])
            return
        suma_enu_prispevok, suma_sf_prispevok, suma_enu_zrazky, suma_sf_zrazky, nzam, pokec, vytvoreny_subor = rslt
        obj.po_zamestnancoch = vytvoreny_subor
        obj.suma_zamestnavatel = -suma_enu_prispevok
        obj.suma_socfond = -suma_sf_prispevok
        obj.zrazka_zamestnavatel = suma_enu_zrazky
        obj.zrazka_socfond = suma_sf_zrazky
        obj.save()
        messages.success(request, f"Vytvorený bol súbor '{Stravne(obj.typ_zoznamu).label}' pre {nzam} zamestnancov. Ak chcete súbor upraviť, stiahnite si ho, upravte a ručne vložte. Sumy v zázname následne upravte podľa novej verzie súboru (neaktualizujú sa automaticky)")

        #vytvoriť alebo aktualizovať súvisiacu položku v účte SF
        rslt = obj.aktualizovat_SF()
        for item in rslt:
            messages.warning(request, 
                format_html(
                    'Pridaná/aktualizovaná bola položka sociálneho fondu č. <em>{}</em>.',
                    mark_safe(f'<a href="/admin/uctovnictvo/socialnyfond/{item[0]}/change/">{item[1]}</a>')
                    )
            )
        self.message_user(request, mark_safe(pokec), messages.INFO)
        self.message_user(request, f"Vytvorenú tabuľku so zoznamom dajte na podpis a potom pred odoslaním vyplňte pole 'Dátum odoslania'. Automaticky sa vytvorí záznam v Denníku prijatej a odoslanej pošty.", messages.SUCCESS)

    generovat_prispevky_zrazky.short_description = "Generovať zoznam príspevkov/zrážok"
    #Oprávnenie na použitie akcie, viazané na 'change'
    generovat_prispevky_zrazky.allowed_permissions = ('change',)

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

@admin.register(Dohodar)
class DohodarAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("priezvisko", "meno", "rod_priezvisko", "suborpriloha", "email", "rodne_cislo", "datum_nar", "miesto_nar", "adresa", "_dochodok", "_ztp","poistovna", "cop", "stav")
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

@admin.register(Vybavovatel)
class VybavovatelAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ["osoba", "telefon", "enu_email"]


@admin.register(Zamestnanec)
class ZamestnanecAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("priezvisko", "meno", "cislo_zamestnanca", "cislo_biometric", "subor_zmluva", "subor_pracnapln", "suborpriloha", "dds", "stupnica", "zamestnanie_od", "zamestnanie_enu_od", "rod_priezvisko", "email", "rodne_cislo", "datum_nar", "miesto_nar", "adresa", "_dochodok", "_ztp","poistovna", "cop", "stav")
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
        #polia_klasif = ["zdroj", "zakazka", "ekoklas", "cinnost"]
        polia_klasif = ["ekoklas", "cinnost"]
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
    #Polia DoVP: odmena_celkom hod_celkom id_tsh
    form = DoVPForm
    def get_list_display(self, request):
        list_display = ("cislo", "zmluvna_strana_link", "odmena_celkom", "hod_celkom", "interny_prevod", "poznamka" )
        return list_display + super(DoVPAdmin, self).get_list_display(request)
    def get_readonly_fields(self, request, obj=None):
        # polia rodičovskej triedy
        ro_parent = super(DoVPAdmin, self).get_readonly_fields(request, obj)
        if not obj:
            return ro_parent
        elif obj.stav_dohody == StavDohody.NOVA or obj.stav_dohody == StavDohody.VYTVORENA: 
            return ro_parent
        elif obj.stav_dohody == StavDohody.NAPODPIS: 
            return ro_parent + ["odmena_celkom", "hod_celkom"]
        elif obj.stav_dohody == StavDohody.ODOSLANA_DOHODAROVI: 
            return ro_parent + ["odmena_celkom", "hod_celkom"]
        elif obj.stav_dohody == StavDohody.PODPISANA_DOHODAROM:
            return ro_parent + ["odmena_celkom", "hod_celkom"]
        elif obj.stav_dohody == StavDohody.DOKONCENA:
            return ro_parent + ["odmena_celkom", "hod_celkom"]
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

    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

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

    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

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
            return ro_parent + ["datum_ukoncenia", "dodatok_k"]
        elif obj.stav_dohody == StavDohody.NAPODPIS: 
            return ro_parent + ["odmena_mesacne", "hod_mesacne", "datum_ukoncenia", "dodatok_k"]
        elif obj.stav_dohody == StavDohody.ODOSLANA_DOHODAROVI: 
            return ro_parent + ["odmena_mesacne", "hod_mesacne", "datum_ukoncenia", "dodatok_k"]
        elif obj.stav_dohody == StavDohody.PODPISANA_DOHODAROM:
            #ro_parent.remove("zdroj")
            #ro_parent.remove("zakazka")
            return ro_parent + ["odmena_mesacne", "hod_mesacne", "dodatok_k"]
        elif obj.stav_dohody == StavDohody.DOKONCENA:
            #ro_parent.remove("zdroj")
            #ro_parent.remove("zakazka")
            return ro_parent + ["odmena_mesacne", "hod_mesacne", "dodatok_k"]
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

    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

    list_totals = [
        ('odmena_mesacne', Sum),
    ]

@admin.register(Nepritomnost)
class NepritomnostAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    form = NepritomnostForm
    list_display = ["cislo", "subor_nepritomnost", "subor_nepritomnost_exp", "nepritomnost_od", "nepritomnost_do", "zamestnanec_link", "nepritomnost_typ", "dlzka_nepritomnosti"]
    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["cislo", "zamestnanec__meno", "zamestnanec__priezvisko", "^nepritomnost_typ"]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('zamestnanec', {
            'admin_order_field': 'zamestnanec__priezvisko', # Allow to sort members by the column
        })
    ]
    actions = ['generovat_nepritomnost', "exportovat_nepritomnost_pre_uctaren"]

    def get_exclude(self, request, obj=None):
        if obj:
            if obj.subor_nepritomnost: 
                return ["zamestnanec", "nepritomnost_od", "nepritomnost_do", "nepritomnost_typ", "dlzka_nepritomnosti"]
            elif obj.zamestnanec:
                return ["subor_nepritomnost", "subor_nepritomnost_exp", "datum_odoslania"]
        return []

    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        #trace()
        AdminForm = super(NepritomnostAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

    #obj is None during the object creation, but set to the object being edited during an edit
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.datum_odoslania:
            return ['cislo', 'subor_nepritomnost_exp'] if request.user.has_perm('uctovnictvo.delete_nepritomnost') else [f.name for f in self.model._meta.fields]
        elif obj:
            return ["cislo", "subor_nepritomnost_exp"]
        else:
            return ["subor_nepritomnost_exp"]

    # Použiť vlastnú message v save_model
    #Potlačí výpis "Objekt ... bol úspešne pridaný"
    #def message_user(self, *args): pass

    def save_model(self, request, obj, form, change):
        #testovať, či náhodou neexistuje neukončená PN
        if obj.zamestnanec: #Vytvorená neprítomnosť
            qs = Nepritomnost.objects.filter(zamestnanec=obj.zamestnanec, 
                                         nepritomnost_typ=TypNepritomnosti.PN,
                                         nepritomnost_do__isnull=True)
            if qs and qs[0].cislo != obj.cislo:
                messages.error(request, f"Neprítomnosť nebola vytvorená, lebo pre zamestnanca {obj.zamestnanec} existuje neukončená PN od {qs[0].nepritomnost_od}.")
                #trace()
                pass
            else:
                super(NepritomnostAdmin, self).save_model(request, obj, form, change)
                messages.success(request, f"Neprítomnosť pre {obj.zamestnanec} bola úspešne vytvorená.")
        #elif obj.subor_nepritomnost and not obj.subor_nepritomnost_exp: #Importovaný zoznam
        elif obj.subor_nepritomnost:
            super(NepritomnostAdmin, self).save_model(request, obj, form, change)
            messages.success(request, f"Importovaný bol súbor so zoznamom neprítomností.")
            messages.warning(request, "Akciou 'Generovať záznamy neprítomnosti' treba vytvoriť jednotlivé záznamy. Ak za daný mesiac pribudnú ešte ďalšie neprítomnosti, treba ich pridať individuálne.")
            messages.warning(request, "Potom, akciou 'Exportovať neprítomnosť pre učtáreň' treba vytvoriť tabuľku pre učtáreň.")

    def generovat_nepritomnost(self, request, queryset):
        if len(queryset) != 1:
            #self.message_user(request, f"Vybrať možno len jednu položku", messages.ERROR)
            messages.error(request, "Vybrať možno len jednu položku")
            return
        polozka = queryset[0]
        # Určiť začiatočné číslo generovaných neprítomností
        uz_generovane = Nepritomnost.objects.filter(cislo__startswith="%s-"%polozka.cislo).order_by("-cislo")
        if uz_generovane:
            zacat_od = int(uz_generovane[0].cislo.split("-")[-1]) + 1
        else:
            zacat_od = 1

        if polozka.subor_nepritomnost:
            rslt = generovatNepritomnost(polozka, zacat_od)
            for msg in rslt:
                self.message_user(request, msg[1], msg[0])
        else:
            messages.error(request, f"Položka {polozka.cislo} neobsahuje súbor so zoznamom neprítomností.")
    generovat_nepritomnost.short_description = "Generovať záznamy neprítomnosti"
    #Oprávnenie na použitie akcie, viazané na 'change'
    generovat_nepritomnost.allowed_permissions = ('change',)

    #generovat mepritomnost (farebnu tabulku) pre uctaren)
    def exportovat_nepritomnost_pre_uctaren(self, request, queryset):
        if len(queryset) != 1:
            #self.message_user(request, f"Vybrať možno len jednu položku", messages.ERROR)
            messages.error(request, "Vybrať možno len jednu položku")
            return
        polozka = queryset[0]
        if not polozka.subor_nepritomnost:
            messages.error(request, f"Položka {polozka.cislo} neobsahuje súbor so zoznamom neprítomností.")

        status, msg, vytvoreny_subor = exportovatNepritomnostUct(polozka)
        if status != messages.ERROR:
            polozka.subor_nepritomnost_exp = vytvoreny_subor
            polozka.save()
        self.message_user(request, msg, status)
    exportovat_nepritomnost_pre_uctaren.short_description = 'Exportovať neprítomnosť pre učtáreň'
    #Oprávnenie na použitie akcie, viazané na 'change'
    exportovat_nepritomnost_pre_uctaren.allowed_permissions = ('change',)

@admin.register(OdmenaOprava)
class OdmenaOpravaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin):
#class OdmenaOpravaAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    form = OdmenaOpravaForm
    list_display = ["cislo", "typ", "zamestnanec_link", "subor_odmeny", "suma", "vyplatene_v_obdobi", "zakazka", "ekoklas", "subor_kl", "datum_kl"]
    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["cislo", "^typ", "zamestnanec__meno", "zamestnanec__priezvisko"]

    # zoraďovateľný odkaz na zamestnanca
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('zamestnanec', {
            'admin_order_field': 'zamestnanec__priezvisko', # Allow to sort members by the column
        })
    ]

    actions = ['vytvorit_kryci_list']

    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(OdmenaOpravaAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

    def vytvorit_kryci_list(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu položku", messages.ERROR)
            return
        polozka = queryset[0]
        if polozka.subor_kl:
            self.message_user(request, f"Krycí list už bol vytvorený, opakovanie nie je možné", messages.ERROR)
            #return
        if polozka.typ in [OdmenaAleboOprava.OPRAVATARIF, OdmenaAleboOprava.OPRAVARIAD, OdmenaAleboOprava.OPRAVAOSOB, OdmenaAleboOprava.OPRAVAZR]:
            self.message_user(request, f"Krycí list sa pre opravy nevytvára.", messages.ERROR)
            return
        #overiť, či nejde o generovaný záznam
        cisla = re.findall(r"(..-....-...)-(..)", polozka.cislo)
        if cisla:
            self.message_user(request, f"Položka {polozka.cislo} je súčasťou {cisla[0][0]}. Samostatný krycí list na nevytvára.", messages.ERROR)
            return
        if polozka.subor_odmeny and polozka.subor_odmeny.file.name.split(".")[-1] == "xlsx": 
            rslt = generovatIndividualneOdmeny(polozka)
            if len(rslt) == 1:  #Chyba
                self.message_user(request, rslt[0], messages.ERROR)
                return
            else:
                pocet, celkova_suma = rslt
                self.message_user(request, f"Vygenerované boli individuálne záznamy o odmenách: počet {pocet}, celková suma {celkova_suma} €.",messages.INFO)
                if celkova_suma != -float(polozka.suma):
                    self.message_user(request, f"Zadaná suma {polozka.suma} € nesúhlasí so súčtom jednotlivých odmien {celkova_suma} € v súbore.",messages.ERROR)

        status, msg, vytvoreny_subor = VytvoritKryciListOdmena(polozka, request.user)
        if status != messages.ERROR:
            ##prispevok.dane_na_uhradu = timezone.now()
            polozka.subor_kl = vytvoreny_subor
            polozka.save()
        self.message_user(request, msg, status)
        #self.message_user(request, f"Generovanie krycích listov ešte nie je implementované",messages.WARNING)
    vytvorit_kryci_list.short_description = "Vytvoriť krycí list (a generovať individuálne odmeny)"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_kryci_list.allowed_permissions = ('change',)

    def delete_queryset(self, request, queryset):
        for qq in queryset:
            if qq.typ ==  OdmenaAleboOprava.ODMENAS:
                pocet = zmazatIndividualneOdmeny(qq)
                self.message_user(request, f"Zmazaných bolo {pocet} individuálnych záznamov o odmenách.",messages.INFO)
            qq.delete()


@admin.register(PrispevokNaRekreaciu)
class PrispevokNaRekreaciuAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ModelAdminTotals):
    form = PrispevokNaRekreaciuForm
    list_display = ["cislo", "zamestnanec_link", "datum", "_subor_ziadost", "datum_podpisu_ziadosti", "_subor_vyuctovanie", "_subor_kl", "datum_kl", "prispevok", "vyplatene_v_obdobi"]
    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["cislo", "zamestnanec__meno", "zamestnanec__priezvisko"]
    list_totals = [
        ('prispevok', Sum),
    ]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('zamestnanec', {
            'admin_order_field': 'zamestnanec__priezvisko', # Allow to sort members by the column
        })
    ]

    actions = ['vytvorit_kryci_list']

    def _subor_vyuctovanie(self, obj):
        if  obj.subor_vyuctovanie:
            url = os.path.join(MEDIA_ROOT,obj.subor_vyuctovanie.url)
            return format_html(mark_safe(f'<a href="{url}">Vyúčtovanie</a>')) 
        else:
            return "-"
    _subor_vyuctovanie.short_description = "Súbor vyúčtovania"

    def _subor_ziadost(self, obj):
        if  obj.subor_ziadost:
            url = os.path.join(MEDIA_ROOT,obj.subor_ziadost.url)
            return format_html(mark_safe(f'<a href="{url}">Žiadosť</a>')) 
        else:
            return "-"
    _subor_ziadost.short_description = "Súbor žiadosti"

    def _subor_kl(self, obj):
        if  obj.subor_kl:
            url = os.path.join(MEDIA_ROOT,obj.subor_kl.url)
            return format_html(mark_safe(f'<a href="{url}">Krycí list</a>')) 
        else:
            return "-"
    _subor_kl.short_description = "Súbor KL"

    # nezobrazovať polia id a program
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        fields.remove('id')
        fields.remove('program')
        return fields

    #['id', 'zdroj', 'program', 'zakazka', 'ekoklas', 'cinnost', 'poznamka', 'cislo', 'datum', 'zamestnanec', 'subor_ziadost', 'subor_vyuctovanie', 'prispevok', 'vyplatene_v_obdobi', 'subor_kl', 'datum_kl']
    def get_readonly_fields(self, request, obj=None):
        fields = [f.name for f in PrispevokNaRekreaciu._meta.get_fields()]
        #fields.remove("id")
        editable = ["poznamka"]
        if not obj:
            editable += ["cislo", "datum", "zamestnanec", "subor_ziadost", "ekoklas", "zdroj", "zakazka"]
        elif obj.subor_ziadost and not obj. datum_podpisu_ziadosti:
            editable += ["datum_podpisu_ziadosti"]
        elif obj.datum_podpisu_ziadosti and not (obj.subor_vyuctovanie and obj.prispevok and obj.vyplatene_v_obdobi):
            editable += ['subor_vyuctovanie', 'prispevok', 'vyplatene_v_obdobi']
        elif obj.prispevok and obj.prispevok > 0:
            editable += ['subor_vyuctovanie', 'prispevok', 'vyplatene_v_obdobi']
        elif obj.subor_kl and not obj.datum_kl:
            editable += ['datum_kl']
        elif obj.subor_kl:  #for the case, when KL was created off-Django and needs to be replaced
            editable += ['subor_kl']
        for rr in editable: fields.remove(rr)
        return fields

    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(PrispevokNaRekreaciuAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

    def vytvorit_kryci_list(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu položku", messages.ERROR)
            return
        prispevok = queryset[0]
        if prispevok.subor_kl:
            self.message_user(request, f"Krycí list už bol vytvorený, opakovanie nie je možné", messages.ERROR)
            return
        status, msg, vytvoreny_subor = VytvoritKryciListRekreacia(prispevok, request.user)
        if status != messages.ERROR:
            #prispevok.dane_na_uhradu = timezone.now()
            prispevok.subor_kl = vytvoreny_subor
            prispevok.save()
        self.message_user(request, msg, status)

    vytvorit_kryci_list.short_description = "Vytvoriť krycí list"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_kryci_list.allowed_permissions = ('change',)

@admin.register(PlatovyVymer)
class PlatovyVymerAdmin(ZobrazitZmeny, AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    form = PlatovyVymerForm
    list_display = ["cislo", "mp","zamestnanec_link", "zamestnanie_enu_od", "stav_vymeru","zamestnanie_od", "aktualna_prax", "datum_postup", "_postup_roky", "_uvazok", "datum_od", "datum_do", "_zamestnanie_roky_dni", "_top", "_ts", "suborvymer"]
    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["cislo", "zamestnanec__meno", "zamestnanec__priezvisko"]
    actions = ['duplikovat_zaznam', 'postup_a_valorizacia_aktualny', 'postup_a_valorizacia_nasledujuci', export_selected_objects]
    # skryť vo formulári na úpravu
    exclude = ["program"]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('zamestnanec', {
            'admin_order_field': 'zamestnanec__priezvisko', # Allow to sort members by the column
        })
    ]

    # Zoradiť položky v pulldown menu
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return formfield_for_foreignkey(self, db_field, request, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.datum_do:
            aux = [f.name for f in PlatovyVymer._meta.get_fields()]
            aux.remove("datum_do")
            aux.remove("zmena_zdroja")
            return aux
        else:
            return ["zamestnanieroky", "zamestnaniedni", "datum_postup"]

    def _uvazok(self, obj):
        return f"{obj.uvazok}/{obj.uvazok_denne}"
    _uvazok.short_description = "Úväzok týždenne/denne"

    def stav_vymeru(self, obj):
        today = date.today()
        if obj.datum_do and obj.datum_do <= today:
            return "Ukončený"
        if obj.datum_od and obj.datum_od > today:
            return "Plánovaný"
        if obj.datum_od and obj.datum_od <= today and (not obj.datum_do or obj.datum_do > today):
            return "Aktívny"
        return "-"
        return obj.zamestnanec.zamestnanie_od.strftime('%d. %m. %Y')
    stav_vymeru.short_description = "Stav výmeru"

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
        spolu = obj.tarifny_plat + obj.osobny_priplatok + obj.funkcny_priplatok
        return f"{obj.tarifny_plat} / {obj.osobny_priplatok} / {obj.funkcny_priplatok} // {spolu}".strip()
    _top.short_description = "Tarifný/osobný/funkčný//spolu"

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
        else:               #vytvorený nový výmer
            # nájsť starý výmer platný k obj.datum_od
            #Výmery, ktorých platnosť začala pred obj.datum_od
            qs = PlatovyVymer.objects.filter(cislo_zamestnanca=obj.cislo_zamestnanca).filter(datum_od__lt=obj.datum_od)
            #Vylúčiť výmery, ktorých platnosť skončila pred obj.datum_od
            qs1 = qs.filter(datum_do__lt=obj.datum_od)
            #vylúčiť qs1 z qs
            qs2 = []
            for vymer in qs:
                if not vymer in qs1:
                    qs2.append(vymer)
            if not qs2: # Pridávame prvý výmer nového zamestnanca
                dp = datum_postupu( obj.zamestnanec.zamestnanie_od, obj.datum_od + timedelta(30))
                #ak ďalší postu už nie je možný, dp je rovné obj.datum_od. Vtedy ho nezobrazovať 
                obj.datum_postup = dp if dp > obj.datum_od else None
            else:
                stary = qs2[0]
                # aktualizácia obj na zaklade udajov v stary
                if stary.datum_do:
                    obj.datum_do = stary.datum_do
                    years, days = vypocet_zamestnanie(obj.zamestnanec.zamestnanie_enu_od, obj.datum_do)
                    obj.zamestnanieroky = years
                    obj.zamestnaniedni = days
                    obj.datum_postup = None
                else:
                    dp = datum_postupu( obj.zamestnanec.zamestnanie_od, obj.datum_od + timedelta(30))
                    #ak ďalší postu už nie je možný, dp je rovné obj.datum_od. Vtedy ho nezobrazovať 
                    obj.datum_postup = dp if dp > obj.datum_od else None
                # ukonciť/skrátiť platnosť starého nastavením datum_do
                stary.datum_do = obj.datum_od-timedelta(1)
                # aktualizácia praxe v stary, hodnotu použiť aj v aktuálnom
                years, days = vypocet_zamestnanie(obj.zamestnanec.zamestnanie_enu_od, stary.datum_do)
                stary.zamestnanieroky = years
                stary.zamestnaniedni = days
                stary.datum_postup = None
                stary.save()
        super(PlatovyVymerAdmin, self).save_model(request, obj, form, change)

    def duplikovat_zaznam(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jeden výmer.", messages.ERROR)
            return
        queryset[0].duplikovat().save()
        self.message_user(request, f"Vytvorený bol nový platový výmer pre {queryset[0].zamestnanec}.", messages.SUCCESS)
    duplikovat_zaznam.short_description = "Duplikovať platobný výmer"
    #Oprávnenie na použitie akcie, viazané na 'change'
    duplikovat_zaznam.allowed_permissions = ('change',)

    #Vytvoriť nové výmery na základe zmeny platového stupňa za nasledujúci rok
    def platovy_postup(self, request, queryset, zr, kr):
        #určiť výmery, ktorých sa to týka
        #začiatok a koniec roka
        tp = TarifnyPlatTabulky(zr.year)
        qs = PlatovyVymer.objects.filter(datum_postup__gte=zr, datum_postup__lte=kr)
        self.message_user(request, f"Nové výmery na základe platového postupu za {zr.year}:", messages.WARNING)
        for stary in qs:
            print(stary.datum_postup)
            novy = stary.duplikovat()
            novy.datum_od = stary.datum_postup
            novy.cislo = nasledujuce_cislo(PlatovyVymer)
            novy.platovy_stupen = stary.platovy_stupen+1
            tarifny = Decimal(tp.TarifnyPlat(novy.datum_od, novy.zamestnanec.stupnica, novy.platova_trieda, novy.platovy_stupen))
            tarifny = tarifny*stary.uvazok/Decimal(UVAZOK_TYZDENNE)
            novy.tarifny_plat = tarifny
            # aktualizácia novy na zaklade udajov v stary
            if stary.datum_do:  #ak je stary ukonceny
                novy.datum_do = stary.datum_do
                years, days = vypocet_zamestnanie(novy.zamestnanec.zamestnanie_enu_od, novy.datum_do)
                novy.zamestnanieroky = years
                novy.zamestnaniedni = days
                novy.datum_postup = None
            else:   #ak stary nie je ukonceny
                dp = datum_postupu( novy.zamestnanec.zamestnanie_od, novy.datum_od + timedelta(30))
                #ak ďalší postup už nie je možný, dp je rovné novy.datum_od. Vtedy ho nezobrazovať 
                novy.datum_postup = dp if dp > novy.datum_od else None
            # ukonciť/skrátiť platnosť starého nastavením datum_do
            stary.datum_do = novy.datum_od-timedelta(1)
            # aktualizácia praxe v stary, hodnotu použiť aj v aktuálnom
            years, days = vypocet_zamestnanie(novy.zamestnanec.zamestnanie_enu_od, stary.datum_do)
            stary.zamestnanieroky = years
            stary.zamestnaniedni = days
            stary.datum_postup = None
            stary.save()
            novy.save()
            self.message_user(request, f"{stary.zamestnanec}: Ukončený výmer č. {stary.cislo} k {stary.datum_do} (trieda {stary.platova_trieda}, stupeň {stary.platovy_stupen}). Nový výmer č. {novy.cislo} platný od {novy.datum_od} (trieda {novy.platova_trieda}, stupeň {novy.platovy_stupen}, stupnica {novy.zamestnanec.stupnica}).", messages.SUCCESS)
        nove_text = ""
        if len(qs):
            nove_text = f"Novovytvoreným výmerom boli priradené čísla v tvare ({PlatovyVymer.oznacenie}-YYYY-NNN). Postupne ich nahraďte CSČ číslami a pridajte súbory výmerov."
        self.message_user(request, f"Počet nových výmerov na základe platového postupu za {zr.year}: {len(qs)}. {nove_text}", messages.WARNING)

    platovy_postup.short_description = "Vytvoriť výmery podľa platového postupu za aktuálny budúci rok"
    #Oprávnenie na použitie akcie, viazané na 'change'
    platovy_postup.allowed_permissions = ('change',)

    #Vytvoriť nové výmery na základe valorizácie za nasledujúci rok
    def valorizacia(self, request, queryset, zr, kr):
        #určiť výmery, ktorých sa to týka
        #začiatok a koniec roka
        tp = TarifnyPlatTabulky(zr.year)
        for dv in tp.DatumyValorizacie():
            if dv < zr: continue
            if dv > kr: continue
            self.message_user(request, f"Nové výmery na základe valorizácie k {dv}:", messages.WARNING)
            #Výmery, do ktorých zasahuje dátum dv
            qs = PlatovyVymer.objects.filter(Q(datum_od__lte=dv, datum_do__gt=dv) | Q(datum_od__lte=dv, datum_do__isnull=True))
            pocet_novych = 0
            for stary in qs:
                if stary.zamestnanec.priezvisko=="Lapúniková":
                    #trace()
                    pass
                #Vylúčiť výmery, ktoré už majú aktuálnu hodnory tarifného
                tarifny = Decimal(tp.TarifnyPlat(dv, stary.zamestnanec.stupnica, stary.platova_trieda, stary.platovy_stupen))
                tarifny = tarifny*stary.uvazok/Decimal(UVAZOK_TYZDENNE)
                if stary.tarifny_plat == tarifny: continue
                pocet_novych += 1
                print(stary.datum_postup)
                novy = stary.duplikovat()
                novy.datum_od = dv
                novy.cislo = nasledujuce_cislo(PlatovyVymer)
                #novy.platovy_stupen = stary.platovy_stupen+1
                #novy.tarifny_plat = tp.TarifnyPlat(novy.datum_od, novy.zamestnanec.stupnica, novy.platova_trieda, novy.platovy_stupen)
                novy.tarifny_plat = tarifny
                # aktualizácia novy na zaklade udajov v stary
                if stary.datum_do:  #ak je stary ukonceny
                    novy.datum_do = stary.datum_do
                    years, days = vypocet_zamestnanie(novy.zamestnanec.zamestnanie_enu_od, novy.datum_do)
                    novy.zamestnanieroky = years
                    novy.zamestnaniedni = days
                    novy.datum_postup = None
                else:   #ak stary nie je ukonceny
                    dp = datum_postupu( novy.zamestnanec.zamestnanie_od, novy.datum_od + timedelta(30))
                    #ak ďalší postup už nie je možný, dp je rovné novy.datum_od. Vtedy ho nezobrazovať 
                    novy.datum_postup = dp if dp > novy.datum_od else None
                # ukonciť/skrátiť platnosť starého nastavením datum_do
                stary.datum_do = novy.datum_od-timedelta(1)
                # aktualizácia praxe v stary, hodnotu použiť aj v aktuálnom
                years, days = vypocet_zamestnanie(novy.zamestnanec.zamestnanie_enu_od, stary.datum_do)
                stary.zamestnanieroky = years
                stary.zamestnaniedni = days
                stary.datum_postup = None
                stary.save()
                print(novy.zamestnanec, novy.__dict__)
                novy.save()
                self.message_user(request, f"{stary.zamestnanec}: Ukončený výmer č. {stary.cislo} k {stary.datum_do} (tarifný plat {stary.tarifny_plat}). Vytvorený nový výmer č. {novy.cislo} platný od {novy.datum_od} (tarifný plat {novy.tarifny_plat}, stupnica {novy.zamestnanec.stupnica}).", messages.SUCCESS)
            nove_text = ""
            if pocet_novych:
                nove_text = f"Novovytvoreným výmerom boli priradené čísla v tvare ({PlatovyVymer.oznacenie}-YYYY-NNN). Postupne ich nahraďte CSČ číslami a pridajte súbory výmerov."
            self.message_user(request, f"Počet nových výmerov na základe platového postupu k {dv}: {pocet_novych}. {nove_text}", messages.WARNING)

    valorizacia.short_description = "Vytvoriť výmery na základe valorizácie za aktuálny rok"
    #Oprávnenie na použitie akcie, viazané na 'change'
    valorizacia.allowed_permissions = ('change',)

    def postup_a_valorizacia_aktualny(self, request, queryset):
        today=date.today()
        zr = date(today.year,1,1)
        kr = date(today.year,12,31)
        self.platovy_postup(request, queryset, zr, kr)
        self.valorizacia(request, queryset, zr, kr)
    postup_a_valorizacia_aktualny.short_description = "Vytvoriť nové výmery na základe platového postupu a valorizácie za aktuálny rok (vyberte ľubovolný výmer)"
    #Oprávnenie na použitie akcie, viazané na 'change'
    postup_a_valorizacia_aktualny.allowed_permissions = ('change',)

    def postup_a_valorizacia_nasledujuci(self, request, queryset):
        today=date.today()
        zr = date(today.year+1,1,1)
        kr = date(today.year+1,12,31)
        self.platovy_postup(request, queryset, zr, kr)
        self.valorizacia(request, queryset, zr, kr)
    postup_a_valorizacia_nasledujuci.short_description = "Vytvoriť nové výmery na základe platového postupu a valorizácie za nasledujúci rok (vyberte ľubovolný výmer)"
    #Oprávnenie na použitie akcie, viazané na 'change'
    postup_a_valorizacia_nasledujuci.allowed_permissions = ('change',)



@admin.register(SocialnyFond)
class SocialnyFondAdmin(ZobrazitZmeny, SimpleHistoryAdmin, ImportExportModelAdmin):
    form = SocialnyFondForm
    list_display = ["cislo", "suma", "datum_platby", "predmet"]
    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["cislo", "predmet"]
