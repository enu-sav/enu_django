from django.contrib import admin

# Register your models here.
from .models import Dokument,TypDokumentu
from .forms import DokumentForm, overit_polozku, parse_cislo
from ipdb import set_trace as trace
from django.utils.html import format_html
from django.utils import timezone
from zmluvy.models import ZmluvaAutor, ZmluvaGrafik, VytvarnaObjednavkaPlatba
from uctovnictvo.models import Objednavka, PrijataFaktura, PrispevokNaStravne, DoVP, DoPC, DoBPS
import re


#priradenie typu dokumentu k jeho označeniu v čísle
typ_dokumentu = {
    ZmluvaAutor.oznacenie: TypDokumentu.AZMLUVA,
    ZmluvaGrafik.oznacenie: TypDokumentu.VZMLUVA,
    VytvarnaObjednavkaPlatba.oznacenie: TypDokumentu.VOBJEDNAVKA,
    Objednavka.oznacenie: TypDokumentu.OBJEDNAVKA,
    PrijataFaktura.oznacenie: TypDokumentu.FAKTURA,
    PrispevokNaStravne.oznacenie: TypDokumentu.ZMLUVA,
    DoPC.oznacenie: TypDokumentu.DoPC,
    DoVP.oznacenie: TypDokumentu.DoVP,
    DoBPS.oznacenie: TypDokumentu.DoBPS
}

#zobrazenie histórie
#https://django-simple-history.readthedocs.io/en/latest/admin.html
from simple_history.admin import SimpleHistoryAdmin

# Ak sa má v histórii zobraziť zoznam zmien, príslušná admin trieda musí dediť od ZobraziZmeny
class ZobrazitZmeny(SimpleHistoryAdmin):
    # v histórii zobraziť zoznam zmenených polí
    history_list_display = ['changed_fields']
    def changed_fields(self, obj):
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            return ", ".join(delta.changed_fields)
        return None

@admin.register(Dokument)
class DokumentAdmin(ZobrazitZmeny):
    form = DokumentForm
    list_display = ["cislo", "cislopolozky", "adresat", "typdokumentu", "inout", "datum", "sposob", "naspracovanie", "zaznamvytvoril", "vec_html", "prijalodoslal", "datumvytvorenia"]
    # určiť poradie polí v editovacom formulári
    #fields = ["cislo"]
    def vec_html(self, obj):
        link = re.findall(r'<a href="([^"]*)">([^<]*)</a>', obj.vec)
        if link:
            return format_html(obj.vec, url=link[0][0])
        else:
            return obj.vec
    search_fields = ("cislo","adresat","sposob", "inout", "prijalodoslal", "vec", "naspracovanie")
    vec_html.short_description = "Popis"
    exclude = ("odosielatel", "url", "prijalodoslal", "datumvytvorenia", "zaznamvytvoril", "poznamka", "typdokumentu")

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(DokumentAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

    # vyplniť polia, ktoré sa nezadávajú vo formulári
    def save_model(self, request, obj, form, change):
        #zámena mien prijalodoslal - zaznamvytvoril
        if obj.datum and not obj.zaznamvytvoril:    #v skutočnosti "Prijal/odoslal"
            obj.zaznamvytvoril = request.user.get_username()
        if not obj.prijalodoslal:    #v skutočnosti "Záznam vytvoril"
            obj.prijalodoslal = request.user.get_username()
        if not obj.datumvytvorenia:
            obj.datumvytvorenia = timezone.now()
        if overit_polozku(obj.cislopolozky): #cislo je podľa schémy X-RRRR-NNN
            td_str = parse_cislo(obj.cislopolozky)[0][0]
            obj.typdokumentu = typ_dokumentu[td_str]
        else:
            obj.typdokumentu = TypDokumentu.INY
        super().save_model(request, obj, form, change)

