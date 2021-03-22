from django.contrib import admin
from ipdb import set_trace as trace
from django.contrib import messages
from django.utils.translation import ngettext

# Register your models here.
from .models import OsobaAutor, ZmluvaAutor
from .common import VytvoritAutorskuZmluvu


class OsobaAutorAdmin(admin.ModelAdmin):
    list_display = ('rs_login', 'rs_uid', 'email', 'titul_pred_menom', 'meno', 'priezvisko', 'titul_za_menom', 'rodne_cislo', 'odbor', "adresa_ulica", "adresa_mesto", "adresa_stat", 'datum_aktualizacie')
    ordering = ('datum_aktualizacie',)
    #search_fields = ('rs_login', 'priezvisko')
    search_fields = ['rs_login', 'r_uid', 'email']
    actions = ['vytvorit_autorsku_zmluvu']

    #obj is None during the object creation, but set to the object being edited during an edit
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["rs_uid", "rs_login"]
        else:
            return []
    def vytvorit_autorsku_zmluvu(self, request, queryset):
        #updated = queryset.update(status='p')
        updated = VytvoritAutorskuZmluvu(queryset)
        #trace()
        self.message_user(request, ngettext(
            'Úspešne vytvorená autorská zmluva: %d',
            'Úspešne vytvorené autorské zmluvy: %d',
            updated,
        ) % updated, messages.SUCCESS)
        pass
    vytvorit_autorsku_zmluvu.short_description = "Vytvoriť autorskú zmluvu a uložiť ju do ..."

admin.site.register(OsobaAutor, OsobaAutorAdmin)

class ZmluvaAutorAdmin(admin.ModelAdmin):
    list_display = ('cislo_zmluvy', 'stav_zmluvy', 'zmluvna_strana', 'odmena', 'datum_pridania', 'datum_aktualizacie')
    ordering = ('datum_aktualizacie',)
    #search_fields = ['cislo_zmluvy']
    search_fields = ['cislo_zmluvy','zmluvna_strana__rs_login', 'odmena', 'stav_zmluvy']

    #obj is None during the object creation, but set to the object being edited during an edit
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["cislo_zmluvy", "zmluvna_strana"]
        else:
            return []

admin.site.register(ZmluvaAutor, ZmluvaAutorAdmin)
