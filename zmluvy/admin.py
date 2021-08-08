from django.contrib import admin
from django.utils import timezone
from django import forms
from ipdb import set_trace as trace
from django.contrib import messages
from django.utils.translation import ngettext
from django.conf import settings
from django.contrib.auth import get_permission_codename
from simple_history.utils import update_change_reason
import os, re
from tempfile import TemporaryFile
import logging

# Register your models here.
# pripajanie suborov k objektu: krok 1, importovať XxxSubor
from .models import OsobaAutor, ZmluvaAutor, PlatbaAutorskaOdmena, PlatbaAutorskaSumar, StavZmluvy, ZmluvaAutorSubor, PlatbaAutorskaSumarSubor, AnoNie, SystemovySubor
from .common import VytvoritAutorskuZmluvu, VyplatitAutorskeOdmeny
from .vyplatitautorske import VyplatitAutorskeOdmeny

#umožniť zobrazenie autora v zozname zmlúv
#https://pypi.org/project/django-admin-relation-links/
from django_admin_relation_links import AdminChangeLinksMixin

#zobrazenie histórie
#https://django-simple-history.readthedocs.io/en/latest/admin.html
from simple_history.admin import SimpleHistoryAdmin

from import_export.admin import ImportExportModelAdmin

# Pridať dodatočné pole popis_zmeny, použije sa ako change_reason v SimpleHistoryAdmin
class OsobaAutorForm(forms.ModelForm):
    #popis_zmeny = forms.CharField()
    popis_zmeny = forms.CharField(widget=forms.TextInput(attrs={'size':80}))
    def save(self, commit=True):
        popis_zmeny = self.cleaned_data.get('popis_zmeny', None)
        # Get the form instance so I can write to its fields
        instance = super(OsobaAutorForm, self).save(commit=commit)
        # this writes the processed data to the description field
        instance._change_reason = popis_zmeny
        return super(OsobaAutorForm, self).save(commit=commit)

    class Meta:
        model = OsobaAutor
        fields = "__all__"

@admin.register(OsobaAutor)
#class OsobaAutorAdmin(AdminChangeLinksMixin, admin.ModelAdmin):
class OsobaAutorAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):

    # modifikovať formulár na pridanie poľa Popis zmeny
    form = OsobaAutorForm
    #Ak pouzijeme 'fields', tak vznikne chyba suvisiaca so 'zmluvy_link' a 'platby_link'
    _fields = (
            'rs_login',
            'titul_pred_menom',
            'meno',
            'priezvisko',
            'titul_za_menom',
            'rodne_cislo',
            'bankovy_kontakt',
            'zdanit',
            'email',
            'rezident',
            'adresa_ulica',
            'adresa_mesto',
            'adresa_stat',
            'koresp_adresa_institucia',
            'koresp_adresa_ulica',
            'koresp_adresa_mesto',
            'koresp_adresa_stat',
            'odbor',
            'preplatok',
            'poznamka'
            )
    #zmluvy_link: pridá odkaz na všetky zmluvy autora do zoznamu
    #platby_link: pridá odkaz na všetky platby autora do zoznamu
    list_display = (
            'rs_login', 'zmluvy_link', 'platby_link', 'preplatok', 'dohodasubor', "datum_dohoda_podpis", "datum_dohoda_oznamenie", 'rezident', 'email',
            'menopriezvisko', 'rodne_cislo', 'odbor', "adresa", "koresp_adresa", 'datum_aktualizacie', 'poznamka'
            )
    ordering = ('datum_aktualizacie',)
    #search_fields = ('rs_login', 'priezvisko')
    #search_fields = ['rs_login', 'r_uid', 'email']
    search_fields = ['rs_login', 'email']

    #Konfigurácia poľa zmluvy_link (pripojené k ZmluvaAutor cez ForeignKey)
    #changelist_links = ['zmluvy'];
    changelist_links = [
        ('zmluvy', {
            'label': 'Zmluvy',  # Used as label for the link
        }),
        ('platby', {
            'label': 'Platby',  # Used as label for the link
        })
    ]

    # zobraziť zoznam zmenených polí
    history_list_display = ['changed_fields']
    def changed_fields(self, obj):
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            return ", ".join(delta.changed_fields)
        return None

    #obj is None during the object creation, but set to the object being edited during an edit
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["rs_uid", "rs_login"]
        else:
            return []

    def menopriezvisko(self, obj):
        if obj.priezvisko:
            mp = f"{obj.titul_pred_menom} {obj.meno} {obj.priezvisko}, {obj.titul_za_menom}".strip()
            mp = mp.replace(", None", "").replace("None ","")
            return mp
    menopriezvisko.short_description = "Meno a tituly"

    def adresa(self, obj):
        if obj.adresa_mesto:
            return f"{obj.adresa_ulica} {obj.adresa_mesto}, {obj.adresa_stat}".strip()
    adresa.short_description = "Trvalé bydlisko"

    def koresp_adresa(self, obj):
        if obj.koresp_adresa_mesto:
            return f"{obj.koresp_adresa_institucia} {obj.koresp_adresa_ulica} {obj.koresp_adresa_mesto}, {obj.koresp_adresa_stat}".strip()
    koresp_adresa.short_description = "Korešp. adresa"

#admin.site.register(OsobaAutor, OsobaAutorAdmin)

# Pridať dodatočné pole popis_zmeny, použije sa ako change_reason v SimpleHistoryAdmin
class ZmluvaAutorForm(forms.ModelForm):
    #popis_zmeny = forms.CharField()
    popis_zmeny = forms.CharField(widget=forms.TextInput(attrs={'size':80}))
    def save(self, commit=True):
        popis_zmeny = self.cleaned_data.get('popis_zmeny', None)
        # Get the form instance so I can write to its fields
        instance = super(ZmluvaAutorForm, self).save(commit=commit)
        # this writes the processed data to the description field
        instance._change_reason = popis_zmeny
        return super(ZmluvaAutorForm, self).save(commit=commit)

    class Meta:
        model = ZmluvaAutor
        fields = "__all__"

# pripajanie suborov k objektu: krok 2, vytvoriť XxxSuborAdmin
# musí byť pred krokom 3
class ZmluvaAutorSuborAdmin(admin.StackedInline):
    model = ZmluvaAutorSubor

@admin.register(ZmluvaAutor)
class ZmluvaAutorAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin, ImportExportModelAdmin):
    # modifikovať formulár na pridanie poľa Popis zmeny
    form = ZmluvaAutorForm
    # zmluvna_strana_link: pridá autora zmluvy do zoznamu, vďaka AdminChangeLinksMixin
    list_display = ('cislo_zmluvy', 'stav_zmluvy', 'zmluvna_strana_link',
            'honorar_ah', 'url_zmluvy_html', 'crz_datum', 'datum_pridania', 'datum_aktualizacie')
    ordering = ('zmluvna_strana',)
    search_fields = ['cislo_zmluvy','zmluvna_strana__rs_login', 'honorar_ah', 'stav_zmluvy']
    actions = ['vytvorit_subory_zmluvy']
    # pripajanie suborov k objektu: krok 3, inline do XxxAdmin 
    inlines = [ZmluvaAutorSuborAdmin]

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
            return ["cislo_zmluvy", "zmluvna_strana", "vygenerovana_subor", "vygenerovana_crz_subor"]
        else:
            return ["vygenerovana_subor", "vygenerovana_crz_subor"]

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

    # zobraziť zoznam zmenených polí
    history_list_display = ['changed_fields']
    def changed_fields(self, obj):
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            return ", ".join(delta.changed_fields)
        return None

    def vytvorit_subory_zmluvy(self, request, queryset):
        for zmluva  in queryset:
            if not zmluva.stav_zmluvy or zmluva.stav_zmluvy == StavZmluvy.VYTVORENA:
                #vytvorene_subory: s cestou vzhľadom na MEDIA_ROOT 'AutorskeZmluvy/AdamAnton-1298/AdamAnton-1298.fodt'
                status, msg, vytvorene_subory = VytvoritAutorskuZmluvu(zmluva)
                if status != messages.ERROR:
                    zmluva.stav_zmluvy = StavZmluvy.VYTVORENA
                    zmluva.datum_aktualizacie = timezone.now(),
                    for subor in vytvorene_subory:
                        if "CRZ" in subor:
                            zmluva.vygenerovana_crz_subor=subor
                        else:
                            zmluva.vygenerovana_subor=subor
                    zmluva.save()
                    #for subor in vytvorene_subory:
                        #novy_subor = ZmluvaAutorSubor(zmluva=zmluva, file=subor)
                        #novy_subor.save()
                self.message_user(request, msg, status)
            else:
                self.message_user(request, f"Súbory zmluvy {zmluva.cislo_zmluvy} neboli vytvorené, lebo zmluva je už v stave '{StavZmluvy(zmluva.stav_zmluvy).label}'", messages.ERROR)
                continue
    vytvorit_subory_zmluvy.short_description = f"Vytvoriť súbory zmluvy"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_subory_zmluvy.allowed_permissions = ('change',)

# pripajanie suborov k objektu: krok 4, register XxxSubor a definicia XxxSuborAdmin
@admin.register(ZmluvaAutorSubor)
class ZmluvaAutorSuborAdmin(admin.ModelAdmin):
    list_display = (["zmluva", "file"])

@admin.register(PlatbaAutorskaOdmena)
class PlatbaAutorskaOdmenaAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin):
    # autor_link: pridá autora zmluvy do zoznamu, vďaka AdminChangeLinksMixin
    list_display = ('autor_link', 'obdobie', 'datum_uhradenia', 'zmluva', 'preplatok_pred', 'honorar', 'odvod_LF', 'odvedena_dan', 'uhradena_suma', 'preplatok_po')

    ordering = ('datum_uhradenia',)

    search_fields = ['obdobie', "zmluva", "autor__rs_login"]

    # zoraďovateľný odkaz na číslo zmluvy
    # umožnené prostredníctvom AdminChangeLinksMixin
    change_links = [
        ('autor', {
            'admin_order_field': 'autor__rs_login', # Allow to sort members by the `autor_link` column
        }),
    ]

    #obj is None during the object creation, but set to the object being edited during an edit
    #predpokladá sa, že hodnoty sa importujú skriptom a že neskôr sa už neupravujú
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['zmluva', 'datum_uhradenia', 'preplatok_pred', 'honorar', 'odvod_LF', 'odvedena_dan', 'uhradena_suma']
        else:
            return []

    # formatovat datum
    def datum_uhradenia(self, obj):
        return obj.datum_uhradenia.strftime("%d-%m-%Y")
    #crz_datum.short_description = "Platná od"

# pripajanie suborov k objektu: krok 2, vytvoriť XxxSuborAdmin
# musí byť pred krokom 3
class PlatbaAutorskaSumarSuborAdmin(admin.StackedInline):
    model = PlatbaAutorskaSumarSubor

# Pridať dodatočné pole popis_zmeny, použije sa ako change_reason v SimpleHistoryAdmin
class PlatbaAutorskaSumarForm(forms.ModelForm):
    #popis_zmeny = forms.CharField()
    popis_zmeny = forms.CharField(widget=forms.TextInput(attrs={'size':80}))
    def save(self, commit=True):
        popis_zmeny = self.cleaned_data.get('popis_zmeny', None)
        # Get the form instance so I can write to its fields
        instance = super(PlatbaAutorskaSumarForm, self).save(commit=commit)
        # this writes the processed data to the description field
        instance._change_reason = popis_zmeny
        return super(PlatbaAutorskaSumarForm, self).save(commit=commit)

    class Meta:
        model = PlatbaAutorskaSumar
        fields = "__all__"

@admin.register(PlatbaAutorskaSumar)
class PlatbaAutorskaSumarAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin):
    form = PlatbaAutorskaSumarForm
    # určiť poradie polí v editovacom formulári
    fields = ['obdobie', 'vyplatit_ths', 'datum_uhradenia', 'vyplatene', 'datum_zalozenia', 'datum_oznamenia', 'import_rs', 'import_webrs', 'datum_importovania', 'popis_zmeny' ]
    list_display = ['obdobie', 'datum_uhradenia', 'datum_zalozenia', 'datum_oznamenia', 'datum_importovania', 'honorar_rs', 'honorar_webrs', 'honorar_spolu', 'vyplatene_spolu', 'odvod_LF', 'odvedena_dan']
    actions = ['vytvorit_podklady_pre_THS', 'zaznamenat_platby_do_db', 'zrusit_platbu']
    # pripajanie suborov k objektu: krok 3, inline do XxxAdmin 
    inlines = [PlatbaAutorskaSumarSuborAdmin]

    def get_inlines(self, request, obj):
        if obj and obj.platba_zaznamenana == AnoNie.ANO:
            return []
        else:
            return self.inlines

    #obj is None during the object creation, but set to the object being edited during an edit
    def get_readonly_fields(self, request, obj=None):
        if obj:
            if obj.platba_zaznamenana == AnoNie.ANO:
                # platba je zaznamenaná, zakázať všetko"
                return ["obdobie", "platba_zaznamenana", "datum_uhradenia", "vyplatene", "vyplatit_ths", "import_webrs", "import_rs"]
            else:
                # povoliť len "datum_uhradenia"
                #return ["obdobie", "platba_zaznamenana"]
                return ["obdobie", "platba_zaznamenana", "vyplatene", "vyplatit_ths", "import_webrs", "import_rs"]
        else:
            # V novej platbe povoliť len "obdobie"
            return ["platba_zaznamenana", "datum_uhradenia"]

    def honorar_spolu(self, sumplatba):
        platby = PlatbaAutorskaOdmena.objects.filter(obdobie=sumplatba.obdobie)
        odmeny = [platba.honorar for platba in platby]
        return sum(odmeny)

    def honorar_rs(self, sumplatba):
        platby = PlatbaAutorskaOdmena.objects.filter(obdobie=sumplatba.obdobie)
        odmeny = [platba.honorar_rs for platba in platby]
        return sum(odmeny)

    def honorar_webrs(self, sumplatba):
        platby = PlatbaAutorskaOdmena.objects.filter(obdobie=sumplatba.obdobie)
        odmeny = [platba.honorar_webrs for platba in platby]
        return sum(odmeny)

    def odvedena_dan(self, sumplatba):
        platby = PlatbaAutorskaOdmena.objects.filter(obdobie=sumplatba.obdobie)
        odmeny = [platba.odvedena_dan for platba in platby]
        return sum(odmeny)

    def odvod_LF(self, sumplatba):
        platby = PlatbaAutorskaOdmena.objects.filter(obdobie=sumplatba.obdobie)
        odmeny = [platba.odvod_LF for platba in platby]
        return sum(odmeny)

    def vyplatene_spolu(self, sumplatba):
        platby = PlatbaAutorskaOdmena.objects.filter(obdobie=sumplatba.obdobie)
        odmeny = [platba.uhradena_suma for platba in platby]
        return sum(odmeny)

    def zaznamenat_platby_do_db(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu platbu", messages.ERROR)
            return
        platba = queryset[0]
        if platba.platba_zaznamenana == AnoNie.ANO:
            self.message_user(request, f"Platba {platba.obdobie} už bola vložená do databázy s dátumom vyplatenia {platba.datum_uhradenia}. Ak chcete platbu opakovane vložiť do databázy, musíte ju zrušit (odstrániť z databázy) pomocou 'Zrušiť platbu'", messages.ERROR)
            return
        if not platba.datum_uhradenia:
            self.message_user(request, f"Platba nebola vložená do databázy, lebo nie je zadaný dátum jej vyplatenia THS-kou. ", messages.ERROR)
            return
        self.vyplatit_autorske_odmeny(request, platba)
        platba.platba_zaznamenana = AnoNie.ANO
        platba.datum_aktualizacie = timezone.now(),
        platba.save()
        pass
    zaznamenat_platby_do_db.short_description = "Zaznamenať platby do databázy"
    #Oprávnenie na použitie akcie, viazané na 'change'
    zaznamenat_platby_do_db.allowed_permissions = ('change',)

    def vytvorit_podklady_pre_THS(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu platbu", messages.ERROR)
            return
        platba = queryset[0]
        if platba.platba_zaznamenana == AnoNie.ANO: 
            self.message_user(request, f"Platba {platba.obdobie} už bola vložená do databázy s dátumom vyplatenia {platba.datum_uhradenia}. Ak chcete opakovane generovať podklady pre THS, platbu najskôr musíte zrušit (odstrániť z databázy) pomocou 'Zrušiť platbu'", messages.ERROR)
            return
        self.vyplatit_autorske_odmeny(request, platba)
        platba.datum_aktualizacie = timezone.now(),
        platba.save()
        pass
    vytvorit_podklady_pre_THS.short_description = "Vytvoriť podklady na vyplatenie autorských odmien pre THS"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vytvorit_podklady_pre_THS.allowed_permissions = ('change',)

    def vyplatit_autorske_odmeny(self, request, platba):
        self.db_logger = logging.getLogger('db')

        #vytvoriť zoznam pripojených súborov
        subory = platba.platbaautorskasumarsubor_set.all()
        nazvy = [subor.file.name for subor in subory]
        try:
            dat_uhradenia = platba.datum_uhradenia.isoformat() if platba.datum_uhradenia else None
            vao = VyplatitAutorskeOdmeny(nazvy)
            vao.vyplatit_odmeny(platba.obdobie, dat_uhradenia)
            logs = vao.get_logs()
            #status, msg, vytvorene_subory = VyplatitAutorskeOdmeny(platba)
            for log in logs:
                fname = re.findall(r"uložené do súboru ({}.*)".format(settings.MEDIA_ROOT),log[1]) 
                if fname:
                    fname = fname[0].replace(settings.MEDIA_ROOT,"")
                    if "THS" in fname:
                        platba.vyplatit_ths = fname
                    elif "Vyplatene" in fname:
                        platba.vyplatene = fname
                    elif "Import-rs" in fname:
                        platba.import_rs = fname
                    elif "Import-webrs" in fname:
                        platba.import_webrs = fname
                        
                self.message_user(request, log[1].replace(settings.MEDIA_ROOT,""), log[0])
            platba.save()
            #self.message_user(request, msg, status)
        except Exception as error:
            self.message_user(request, error, messages.ERROR)
        pass
        #for zmluva  in queryset:

    def zrusit_platbu(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, f"Vybrať možno len jednu platbu", messages.ERROR)
            return
        platba = queryset[0]
        if platba.platba_zaznamenana == AnoNie.NIE: 
            self.message_user(request, f"Platbu {platba.obdobie} nemožno zrušiť, lebo ešte nebola vložená do databázy", messages.ERROR)
            return
        vao = VyplatitAutorskeOdmeny()
        vao.zrusit_vyplacanie(platba.obdobie)
        platba.datum_uhradenia = None
        platba.datum_importovania = None
        platba.datum_zalozenia = None
        platba.datum_oznamenia = None
        platba.platba_zaznamenana = AnoNie.NIE
        #odstrániť súbory
        platba.vyplatit_ths.delete()
        platba.vyplatene.delete()
        platba.import_rs.delete()
        platba.import_webrs.delete()
        platba.vyplatit_ths=None
        platba.vyplatene=None
        platba.import_rs=None
        platba.import_webrs=None
        pass
        platba.save()
        logs = vao.get_logs()
        for log in logs:
            self.message_user(request, log[1].replace(settings.MEDIA_ROOT,""), log[0])
        #self.message_user(request, f"Platba {platba.obdobie} bola zrušená", messages.INFO)
    zrusit_platbu.short_description = "Zrušiť záznam o platbách v databáze"
    #Oprávnenie na použitie akcie, viazané na 'delete'
    zrusit_platbu.allowed_permissions = ('delete',)


# pripajanie suborov k objektu: krok 4, register XxxSubor a definicia XxxSuborAdmin
@admin.register(PlatbaAutorskaSumarSubor)
class PlatbaAutorskaSumarSuborAdmin(admin.ModelAdmin):
    list_display = (["file", "platba_autorska_sumar"])
    def get_readonly_fields(self, request, obj=None):
        return ["platba_autorska_sumar", "file"]

@admin.register(SystemovySubor)
class SystemovySuborAdmin(admin.ModelAdmin):
    list_display = ("subor_nazov", "subor_popis", "subor")
    fields = ("subor_nazov", "subor_popis", "subor")
    # názov sa nesmie meniť, podľa názvu sa v kóde súbor vyhľadáva
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["subor_nazov"]
        else:
            return []

