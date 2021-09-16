from django.contrib import admin 
from django import forms
from ipdb import set_trace as trace
from .models import EkonomickaKlasifikacia, Transakcia, TypZakazky, Zdroj, Program, Dodavatel, Objednavka, TrvalaZmluva

#zobrazenie histórie
#https://django-simple-history.readthedocs.io/en/latest/admin.html
from simple_history.admin import SimpleHistoryAdmin

from import_export.admin import ImportExportModelAdmin

from totalsum.admin import TotalsumAdmin

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

@admin.register(Transakcia)
class TransakciaAdmin(SimpleHistoryAdmin, ImportExportModelAdmin, AdminChangeLinksMixin, ModelAdminTotals):
#class TransakciaAdmin(SimpleHistoryAdmin, AdminChangeLinksMixin, ModelAdminTotals):
    list_display = ("popis", "datum", "suma", "zdroj", "program", "zakazka", "ekoklas_link")
    list_totals = [
            ('suma', Sum),
            ]
    totalsum_list = ('suma',)
    unit_of_measure = '&euro;'

    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["^zdroj__kod", "^program__kod", "^zakazka__kod", "^ekoklas__kod"]

    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('ekoklas', {
            'admin_order_field': 'ekoklas__kod',  # Allow to sort members by `zmluvna_strana_link` column
        })
    ]

@admin.register(Dodavatel)
class DodavatelAdmin(SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("nazov", "bankovy_kontakt", "adresa") 
    search_fields = ("nazov",)
    def adresa(self, obj):
        if obj.adresa_mesto:
            return f"{obj.adresa_ulica} {obj.adresa_mesto}, {obj.adresa_stat}".strip()
    adresa.short_description = "Adresa"

@admin.register(Objednavka)
#class ObjednavkaAdmin(admin.ModelAdmin):
#class ObjednavkaAdmin(SimpleHistoryAdmin,AdminChangeLinksMixin):
class ObjednavkaAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("cislo", "dodavatel_link",)
    #def formfield_for_dbfield(self, db_field, **kwargs):
        #formfield = super(ObjednavkaAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        #if db_field.name == 'objednane_polozky':
            #formfield.widget = forms.Textarea(attrs=formfield.widget.attrs)
        #return formfield

    # ^: v poli vyhľadávať len od začiatku
    search_fields = ["^dodavatel__nazov"]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('dodavatel', {
            'admin_order_field': 'dodavatel__nazov', # Allow to sort members by the `dodavatel_link` column
        })
    ]

@admin.register(TrvalaZmluva)
#class TrvalaZmluvaAdmin(admin.ModelAdmin):
#class TrvalaZmluvaAdmin(SimpleHistoryAdmin,AdminChangeLinksMixin):
class TrvalaZmluvaAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("cislo", "dodavatel_link",)
    search_fields = ["^dodavatel__nazov"]

    # zoraďovateľný odkaz na dodávateľa
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('dodavatel', {
            'admin_order_field': 'dodavatel__nazov', # Allow to sort members by the `dodavatel_link` column
        })
    ]
