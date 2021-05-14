from django.contrib import admin
from ipdb import set_trace as trace
from django.contrib import messages
from django.utils.translation import ngettext

# Register your models here.
from beliana import settings
from .models import OsobaAutor, ZmluvaAutor, PlatbaAutorskaOdmena

#umožniť zobrazenie autora v zozname zmlúv
#https://pypi.org/project/django-admin-relation-links/
from django_admin_relation_links import AdminChangeLinksMixin

#zobrazenie histórie
#https://django-simple-history.readthedocs.io/en/latest/admin.html
from simple_history.admin import SimpleHistoryAdmin

@admin.register(OsobaAutor)
#class OsobaAutorAdmin(AdminChangeLinksMixin, admin.ModelAdmin):
class OsobaAutorAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin):
    #zmluvy_link: pridá odkaz na všetky zmluvy autora do zoznamu
    list_display = ('rs_login', 'rs_uid', 'zmluvy_link', 'email', 'titul_pred_menom', 'meno', 'priezvisko', 'titul_za_menom', 'rodne_cislo', 'odbor', "adresa_ulica", "adresa_mesto", "adresa_stat", 'datum_aktualizacie', 'zdanit', 'preplatok', 'poznamka')
    ordering = ('datum_aktualizacie',)
    #search_fields = ('rs_login', 'priezvisko')
    #search_fields = ['rs_login', 'r_uid', 'email']
    search_fields = ['rs_login', 'email']
    actions = ['vytvorit_autorsku_zmluvu']

    #Konfigurácia poľa zmluvy_link (pripojené k ZmluvaAutor cez ForeignKey)
    #changelist_links = ['zmluvy'];
    changelist_links = [
        ('zmluvy', {
            'label': 'Zmluvy',  # Used as label for the link
        })
    ]

    #obj is None during the object creation, but set to the object being edited during an edit
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["rs_uid", "rs_login"]
        else:
            return []
    def vytvorit_autorsku_zmluvu(self, request, queryset):
        #updated = queryset.update(status='p')
        success=0
        failed=0
        for autor  in queryset:
            status, msg = autor.VytvoritZmluvu("999", "540")
            if status == messages.ERROR:
                self.message_user(request, msg, status)
                failed += 1
            else:
                self.message_user(request, msg, status)
                success += 1

        #trace()
        if success:
            self.message_user(request, ngettext(
                'Úspešne vytvorené autorské zmluvy: %d',
                'Úspešne vytvorené autorské zmluvy: %d',
                success,
            ) % success, messages.SUCCESS)
        pass
    vytvorit_autorsku_zmluvu.short_description = f"Vytvoriť autorskú zmluvu"
#admin.site.register(OsobaAutor, OsobaAutorAdmin)

@admin.register(ZmluvaAutor)
class ZmluvaAutorAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin):
    # zmluvna_strana_link: pridá autora zmluvy do zoznamu, vďaka AdminChangeLinksMixin
    list_display = ('cislo_zmluvy', 'stav_zmluvy', 'zmluvna_strana_link', 'odmena', 'url_zmluvy_html', 'crz_datum', 'datum_pridania', 'datum_aktualizacie')
    ordering = ('zmluvna_strana',)
    #search_fields = ['cislo_zmluvy']
    search_fields = ['cislo_zmluvy','zmluvna_strana__rs_login', 'odmena', 'stav_zmluvy']

    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = ['zmluvna_strana']
    change_links = [
        ('zmluvna_strana', {
            'admin_order_field': 'zmluvna_strana__rs_login',  # Allow to sort members by `zmluvna_strana_link` column
        })
    ]

    #obj is None during the object creation, but set to the object being edited during an edit
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["cislo_zmluvy", "zmluvna_strana"]
        else:
            return []

    # formátovať pole url_zmluvy
    def url_zmluvy_html(self, obj):
        from django.utils.html import format_html
        result = ZmluvaAutor.objects.filter(cislo_zmluvy=obj)
        if result and result[0].url_zmluvy:
            result = result[0]
            return format_html(f'<a href="{result.url_zmluvy}" target="_blank">pdf</a>')
        else:
            return None
    url_zmluvy_html.short_description = "Zmluva v CRZ"

    # formatovat datum
    def crz_datum(self, obj):
        result = ZmluvaAutor.objects.filter(cislo_zmluvy=obj)
        if result and result[0].datum_zverejnenia_CRZ:
            result = result[0]
            return obj.datum_zverejnenia_CRZ.strftime("%d-%m-%Y")
        else:
            return None
    crz_datum.short_description = "Platná od"

@admin.register(PlatbaAutorskaOdmena)
class PlatbaAutorskaOdmenaAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin):
    # zmluvna_strana_link: pridá autora zmluvy do zoznamu, vďaka AdminChangeLinksMixin
    list_display = ('datum_uhradenia', 'zmluva_link', 'preplatok_pred', 'odmena', 'odvod_LF', 'odvedena_dan', 'uhradena_suma')

    ordering = ('datum_uhradenia',)

    #search_fields = ['cislo_zmluvy']
    #search_fields = ['cislo_zmluvy','zmluvna_strana__rs_login', 'odmena', 'stav_zmluvy']

    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = ['zmluva']
    change_links = [
        ('zmluva', {
            'admin_order_field': 'zmluva__cislo_zmluvy',  # Allow to sort members by `zmluvna_strana_link` column
        })
    ]

    #obj is None during the object creation, but set to the object being edited during an edit
    #def get_readonly_fields(self, request, obj=None):
        #if obj:
            #return ["cislo_zmluvy", "zmluvna_strana"]
        #else:
            #return []

    # formatovat datum
    #def crz_datum(self, obj):
        #result = ZmluvaAutor.objects.filter(cislo_zmluvy=obj)
        #if result and result[0].datum_zverejnenia_CRZ:
            #result = result[0]
            #return obj.datum_zverejnenia_CRZ.strftime("%d-%m-%Y")
        #else:
            #return None
    #crz_datum.short_description = "Platná od"
