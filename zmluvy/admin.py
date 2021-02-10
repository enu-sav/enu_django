from django.contrib import admin

# Register your models here.
from .models import Osoba, Zmluva


class OsobaAdmin(admin.ModelAdmin):
    list_display = ('rs_uid', 'rs_login', 'email', 'titul_pred_menom', 'meno', 'priezvisko', 'titul_za_menom', 'posobisko', 'datum_pridania', 'datum_aktualizacie')
    ordering = ('datum_aktualizacie',)
    #search_fields = ('rs_login', 'priezvisko')
    search_fields = ['rs_login']

admin.site.register(Osoba, OsobaAdmin)

class ZmluvaAdmin(admin.ModelAdmin):
    list_display = ('zmluvna_strana', 'cislo_zmluvy', 'datum_pridania', 'datum_aktualizacie')
    ordering = ('datum_aktualizacie',)
    search_fields = ['cislo_zmluvy']

admin.site.register(Zmluva, ZmluvaAdmin)

#admin.site.register(Osoba)
#admin.site.register(Zmluva)
