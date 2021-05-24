from django.contrib import admin
from django import forms
from ipdb import set_trace as trace
from django.contrib import messages
from django.utils.translation import ngettext
from simple_history.utils import update_change_reason

# Register your models here.
from beliana import settings
from .models import OsobaAutor, ZmluvaAutor, PlatbaAutorskaOdmena, PlatbaAutorskaSumar

#umožniť zobrazenie autora v zozname zmlúv
#https://pypi.org/project/django-admin-relation-links/
from django_admin_relation_links import AdminChangeLinksMixin

#zobrazenie histórie
#https://django-simple-history.readthedocs.io/en/latest/admin.html
from simple_history.admin import SimpleHistoryAdmin

# Pridať dodatočné pole popis_zmeny, použije sa ako change_reason v SimpleHistoryAdmin
class OsobaAutorForm(forms.ModelForm):
    #popis_zmeny = forms.CharField()
    popis_zmeny = forms.CharField(widget=forms.TextInput(attrs={'size':80}))
    def save(self, commit=True):
        popis_zmeny = self.cleaned_data.get('popis_zmeny', None)
        #trace()
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
class OsobaAutorAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin):

    # modifikovať formulár na pridanie poľa Popis zmeny
    form = OsobaAutorForm
    #zmluvy_link: pridá odkaz na všetky zmluvy autora do zoznamu
    #platby_link: pridá odkaz na všetky platby autora do zoznamu
    list_display = (
            'rs_login', 'rs_uid', 'zmluvy_link', 'platby_link', 'preplatok', 'zdanit', 'email', 
            'titul_pred_menom', 'meno', 'priezvisko', 'titul_za_menom', 
            'rodne_cislo', 'odbor', "adresa_ulica", "adresa_mesto", 
            "adresa_stat", 'datum_aktualizacie', 'poznamka'
            )
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

# Pridať dodatočné pole popis_zmeny, použije sa ako change_reason v SimpleHistoryAdmin
class ZmluvaAutorForm(forms.ModelForm):
    #popis_zmeny = forms.CharField()
    popis_zmeny = forms.CharField(widget=forms.TextInput(attrs={'size':80}))
    def save(self, commit=True):
        popis_zmeny = self.cleaned_data.get('popis_zmeny', None)
        #trace()
        # Get the form instance so I can write to its fields
        instance = super(ZmluvaAutorForm, self).save(commit=commit)
        # this writes the processed data to the description field
        instance._change_reason = popis_zmeny
        return super(ZmluvaAutorForm, self).save(commit=commit)

    class Meta:
        model = ZmluvaAutor
        fields = "__all__"

@admin.register(ZmluvaAutor)
class ZmluvaAutorAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin):
    # modifikovať formulár na pridanie poľa Popis zmeny
    form = ZmluvaAutorForm
    # zmluvna_strana_link: pridá autora zmluvy do zoznamu, vďaka AdminChangeLinksMixin
    list_display = ('cislo_zmluvy', 'stav_zmluvy', 'zmluvna_strana_link', 
            'honorar_ah', 'url_zmluvy_html', 'crz_datum', 'datum_pridania', 'datum_aktualizacie')
    ordering = ('zmluvna_strana',)
    search_fields = ['cislo_zmluvy','zmluvna_strana__rs_login', 'honorar_ah', 'stav_zmluvy']

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

    # zobraziť zoznam zmenených polí
    history_list_display = ['changed_fields']
    def changed_fields(self, obj):
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            return ", ".join(delta.changed_fields)
        return None

@admin.register(PlatbaAutorskaOdmena)
class PlatbaAutorskaOdmenaAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin):
    # autor_link: pridá autora zmluvy do zoznamu, vďaka AdminChangeLinksMixin
    list_display = ('datum_uhradenia', 'obdobie', 'zmluva', 'autor_link', 'preplatok_pred', 'honorar', 'odvod_LF', 'odvedena_dan', 'uhradena_suma', 'preplatok_po')

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

@admin.register(PlatbaAutorskaSumar)
class PlatbaAutorskaSumarAdmin(AdminChangeLinksMixin, SimpleHistoryAdmin):
    list_display = ['obdobie', 'datum_uhradenia', 'honorar_rs', 'honorar_webrs', 'honorar_spolu', 'vyplatene_spolu', 'odvod_LF', 'odvedena_dan']

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
