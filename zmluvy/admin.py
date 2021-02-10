from django.contrib import admin

# Register your models here.
from .models import Osoba, Zmluva


class OsobaAdmin(admin.ModelAdmin):
    list_display = ('rs_login', 'rs_uid', 'email', 'titul_pred_menom', 'meno', 'priezvisko', 'titul_za_menom', 'posobisko', 'datum_pridania', 'datum_aktualizacie')
    ordering = ('datum_aktualizacie',)
    #search_fields = ('rs_login', 'priezvisko')
    search_fields = ['rs_login']

    #obj is None during the object creation, but set to the object being edited during an edit
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["rs_uid", "rs_login"]
        else:
            return []

admin.site.register(Osoba, OsobaAdmin)

class ZmluvaAdmin(admin.ModelAdmin):
    list_display = ('cislo_zmluvy', 'zmluvna_strana', 'datum_pridania', 'datum_aktualizacie')
    ordering = ('datum_aktualizacie',)
    search_fields = ['cislo_zmluvy']

    #obj is None during the object creation, but set to the object being edited during an edit
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["cislo_zmluvy", "zmluvna_strana"]
        else:
            return []

admin.site.register(Zmluva, ZmluvaAdmin)

#admin.site.register(Osoba)
#admin.site.register(Zmluva)
