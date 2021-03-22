from django.contrib import admin

# Register your models here.
from .models import OsobaAutor, ZmluvaAutor


class OsobaAutorAdmin(admin.ModelAdmin):
    list_display = ('rs_login', 'rs_uid', 'email', 'titul_pred_menom', 'meno', 'priezvisko', 'titul_za_menom', 'rodne_cislo', 'odbor', "adresa_ulica", "adresa_mesto", "adresa_stat", 'datum_aktualizacie')
    ordering = ('datum_aktualizacie',)
    #search_fields = ('rs_login', 'priezvisko')
    search_fields = ['rs_login', 'r_uid', 'email']

    #obj is None during the object creation, but set to the object being edited during an edit
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["rs_uid", "rs_login"]
        else:
            return []

admin.site.register(OsobaAutor, OsobaAutorAdmin)

class ZmluvaAutorAdmin(admin.ModelAdmin):
    list_display = ('cislo_zmluvy', 'zmluvna_strana', 'odmena', 'datum_pridania', 'datum_aktualizacie')
    ordering = ('datum_aktualizacie',)
    #search_fields = ['cislo_zmluvy']
    search_fields = ['cislo_zmluvy','zmluvna_strana__rs_login', 'odmena']

    #obj is None during the object creation, but set to the object being edited during an edit
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["cislo_zmluvy", "zmluvna_strana"]
        else:
            return []

admin.site.register(ZmluvaAutor, ZmluvaAutorAdmin)
