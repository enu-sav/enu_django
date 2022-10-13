from django.contrib import admin

# Register your models here.
from .models import Dokument,TypDokumentu, TypFormulara, Formular, CerpanieRozpoctu, PlatovaRekapitulacia
from .forms import DokumentForm, FormularForm, overit_polozku, parse_cislo
from .export_xlsx import export_as_xlsx
from dennik.common import VyplnitAVygenerovat
from ipdb import set_trace as trace
from django.utils.html import format_html
from django.utils import timezone
from django.contrib import messages
from zmluvy.models import ZmluvaAutor, ZmluvaGrafik, VytvarnaObjednavkaPlatba, PlatbaAutorskaSumar
from uctovnictvo.models import Objednavka, PrijataFaktura, PrispevokNaStravne, DoVP, DoPC, DoBPS
from uctovnictvo.models import PlatovyVymer, PravidelnaPlatba, NajomneFaktura, InternyPrevod
from uctovnictvo.models import RozpoctovaPolozka, PlatbaBezPrikazu, Pokladna, PrispevokNaRekreaciu, OdmenaOprava
import re
from import_export.admin import ImportExportModelAdmin
from datetime import date
from collections import defaultdict

from admin_totals.admin import ModelAdminTotals
from django.db.models import Sum

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from django.http import HttpResponse
from decimal import Decimal

from PyPDF2 import PdfFileReader

#https://pypi.org/project/django-admin-rangefilter/
from rangefilter.filters import DateRangeFilter

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
    DoBPS.oznacenie: TypDokumentu.DoBPS,
    PlatbaAutorskaSumar.oznacenie: TypDokumentu.VYPLACANIE_AH,
    PravidelnaPlatba.oznacenie: TypDokumentu.PRAVIDELNAPLATBA,
    InternyPrevod.oznacenie: TypDokumentu.INTERNYPREVOD,
    NajomneFaktura.oznacenie: TypDokumentu.NAJOMNE,
    PrispevokNaRekreaciu.oznacenie: TypDokumentu.REKREACIA 
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
class DokumentAdmin(ZobrazitZmeny,ImportExportModelAdmin):
    form = DokumentForm
    list_display = ["cislo", "cislopolozky", "adresat", "typdokumentu", "inout", "datum", "sposob", "naspracovanie", "zaznamvytvoril", "vec_html", "suborposta", "prijalodoslal", "datumvytvorenia"]
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
    exclude = ("odosielatel", "url", "prijalodoslal", "datumvytvorenia", "zaznamvytvoril", "poznamka")

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
        elif not obj.typdokumentu:
            obj.typdokumentu = TypDokumentu.INY
        super().save_model(request, obj, form, change)

#Hromadný dokument
@admin.register(Formular)
class FormularAdmin(ZobrazitZmeny):
    form = FormularForm
    list_display = ["cislo", "subor_nazov", "typformulara", "na_odoslanie", "sablona", "data", "vyplnene", "vyplnene_data", "rozposlany", "data_komentar"]
    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return ["na_odoslanie", "vyplnene", "vyplnene_data", "rozposlany", "data_komentar"]
        elif not obj.vyplnene:
            return ["cislo", "subor_nazov", "typformulara", "na_odoslanie", "vyplnene", "vyplnene_data", "rozposlany", "data_komentar"]
        elif obj.na_odoslanie:
            return ["cislo", "typformulara", "subor_nazov", "sablona", "data", "vyplnene", "vyplnene_data", "na_odoslanie"]
        else:
            return ["cislo", "typformulara", "subor_nazov", "vyplnene", "vyplnene_data"]

    actions = ['vyplnit_a_vygenerovat']

    def vyplnit_a_vygenerovat(self, request, queryset):
        if len(queryset) != 1:
            messages.error(request, f"Vybrať možno len jednu položku")
            return
        formular = queryset[0]
        status, msg, vyplnene, vyplnene_data = VyplnitAVygenerovat(formular)
        self.message_user(request, msg, status)
        if status != messages.ERROR:
            formular.vyplnene = vyplnene
            formular.vyplnene_data = vyplnene_data
            formular.save()
            if formular.typformulara == TypFormulara.VSEOBECNY: 
                #Použité dáta sú totožné so vstupnými dátami.
                messages.warning(request, format_html("Vo výstupnom fodt súbore 'Vytvorený súbor' skontrolujte stránkovanie a ak treba, tak ho upravte.<br />Po kontrole súbor vytlačte (prípadne ešte raz skontrolujte vytlačené), dajte na sekretarát na rozposlanie a vyplňte dátum v poli 'Na odoslanie dňa'. Tým sa vytvorí záznam v <em>Denníku prijatej a odoslanej pošty</em>, kam sekretariát doplní dátum rozposlania."))
            else:
                #Použité dáta sú celkom alebo čiastočne prevzaté z databázy.
                messages.warning(request, format_html("Vo výstupnom fodt súbore 'Vytvorený súbor' skontrolujte stránkovanie a ak treba, tak ho upravte.<br />Správnosť dát prevzatých z databázy Djanga skontrolujte vo výstupnom xlsx súbore 'Vyplnené dáta'."))
        else:
            messages.error(request, "Súbory neboli vytvorené.")

    vyplnit_a_vygenerovat.short_description = "Vytvoriť súbor hromadného dokumentu"
    #Oprávnenie na použitie akcie, viazané na 'change'
    vyplnit_a_vygenerovat.allowed_permissions = ('change',)

    # do AdminForm pridať request, aby v jej __init__ bolo request dostupné
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(FormularAdmin, self).get_form(request, obj, **kwargs)
        class AdminFormMod(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return AdminFormMod

@admin.register(CerpanieRozpoctu)
class CerpanieRozpoctuAdmin(ModelAdminTotals):
    list_display = ["polozka","mesiac","suma","zdroj","zakazka","ekoklas"]
    #search_fields = ["polozka", "mesiac", "zdroj", "zakazka", "ekoklas"]
    search_fields = ["polozka", "mesiac", "^zdroj__kod", "^zakazka__kod", "^ekoklas__kod"]
    actions = ['generovat2021', "generovat2022", export_as_xlsx]
    list_totals = [
            ('suma', Sum)
            ]
    list_filter = (
        ('mesiac', DateRangeFilter),
    )
    #stránkovanie a 'Zobraziť všetko'
    list_per_page = 50
    list_max_show_all = 100000

    def generovat2021(self, request, queryset):
        self.generovat(request, 2021)
        pass
    generovat2021.short_description = f"Generovať prehľad čerpania rozpočtu za 2021"
    generovat2021.allowed_permissions = ('change',)

    def generovat2022(self, request, queryset):
        return self.generovat(request, 2022)
        pass
    generovat2022.short_description = f"Generovať prehľad čerpania rozpočtu za 2022"
    generovat2022.allowed_permissions = ('change',)

    def generovat(self,request,rok):
        def zapisat_riadok(ws, fw, riadok, polozky, header=False):
            for cc, value in enumerate(polozky):
                ws.cell(row=riadok, column = cc+1).value = value 
                if isinstance(value, date):
                    ws.cell(row=riadok, column=cc+1).value = value
                    ws.cell(row=riadok, column=cc+1).number_format = "DD-MM-YYYY"
                    if not cc in fw: fw[cc] = 0
                    if fw[cc] < 12: fw[cc] = 12 
                elif type(value) == Decimal:
                    ws.cell(row=riadok, column=cc+1).value = value
                    ws.cell(row=riadok, column=cc+1).number_format="0.00"
                    if not cc in fw: fw[cc] = 0
                    if fw[cc] < 12: fw[cc] = 12 
                else:
                    ws.cell(row=riadok, column=cc+1).value = str(value)
                    if not cc in fw: fw[cc] = 0
                    if fw[cc] < len(str(value))+2: fw[cc] = len(str(value))+2
    
        #najskôr všetko zmazať
        CerpanieRozpoctu.objects.filter(mesiac__isnull=False).delete()

        #Vytvoriť workbook
        file_name = f"Cerpanie_rozpoctu_{rok}-{date.today().isoformat()}"
        wb = Workbook()
        ws_prehlad = wb.active
        ws_prehlad.title = "Prehľad"
        ws_polozky = wb.create_sheet(title="Položky")

        # 1. deň v mesiaci
        md1list = [date(rok, mm+1, 1) for mm in range(12)]
        md1list.append(date(rok+1, 1, 1))

        cerpanie = defaultdict(dict)
        nazvy = ["Názov", "Suma", "Subjekt", "Dátum", "Číslo", "Zdroj", "Zákazka", "Klasifikácia"]
        fw = {}
        zapisat_riadok(ws_polozky, fw, 1, nazvy, header=True)
        riadok=2
        #for fn in enumerate(nazvy): fw[fn[0]]=len(fn[1])

        typy = [PravidelnaPlatba, PlatovyVymer, OdmenaOprava, PrijataFaktura, DoVP, DoPC, PlatbaAutorskaSumar, NajomneFaktura, PrispevokNaStravne, RozpoctovaPolozka, PlatbaBezPrikazu, Pokladna, PrispevokNaRekreaciu,InternyPrevod]
        for typ in typy:
            for polozka in typ.objects.filter():
                for md1 in md1list[:-1]:
                    data = polozka.cerpanie_rozpoctu(md1)
                    for item in data:
                        identif = f"{item['nazov']} {item['zdroj'].kod} {item['zakazka'].kod} {item['ekoklas'].kod}, {md1}"
                        polozky = [item['nazov'], item['suma'], item['subjekt'] if "subjekt" in item else "", item['datum'] if "datum" in item else "", item['cislo'], item['zdroj'].kod, item['zakazka'].kod, item['ekoklas'].kod]
                        zapisat_riadok(ws_polozky, fw, riadok, polozky)
                        riadok +=1

                        if not identif in cerpanie:
                            cerpanie[identif] = item
                            cerpanie[identif]['md1'] = md1
                        else:
                            cerpanie[identif]['suma'] += item['suma']
                        if 'poznamka' in  item:
                            messages.warning(request, format_html(item['poznamka']))
        for cc in fw:
            ws_polozky.column_dimensions[get_column_letter(cc+1)].width = fw[cc]

        # zapísať do databázy a do ws_prehlad
        nazvy = ["Názov", "Mesiac", "Suma", "Zdroj", "Zákazka", "Klasifikácia"]
        fw = {}
        zapisat_riadok(ws_prehlad, fw, 1, nazvy, header=True)
        riadok=2
        # Ak ide o Dotáciu, nepriradiť dátum
        for item in cerpanie:
            cr = CerpanieRozpoctu (
                unikatny = item,
                polozka = cerpanie[item]['nazov'],
                mesiac = None if "Dotácia" in item else cerpanie[item]['md1'],
                suma = cerpanie[item]['suma'],
                zdroj = cerpanie[item]['zdroj'],
                zakazka = cerpanie[item]['zakazka'],
                ekoklas = cerpanie[item]['ekoklas'],
                ).save()
            polozky = [cerpanie[item]['nazov'], cerpanie[item]['md1'], cerpanie[item]['suma'], cerpanie[item]['zdroj'].kod, cerpanie[item]['zakazka'].kod, cerpanie[item]['ekoklas'].kod]
            zapisat_riadok(ws_prehlad, fw, riadok, polozky)
            riadok +=1
        for cc in fw:
            ws_prehlad.column_dimensions[get_column_letter(cc+1)].width = fw[cc]

        #Uložiť a zobraziť 
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={file_name}.xlsx'
        wb.save(response)
        return response

    # Nemazať  "Pomocná položka", potrebujeme
    def delete_queryset(self, request, queryset):
        for qq in queryset:
            if qq.polozka != "Pomocná položka":
                qq.delete()

@admin.register(PlatovaRekapitulacia)
class PlatovaRekapitulaciaAdmin(ModelAdminTotals):
    list_display = ["identifikator","subor"]
    search_fields = ["^identifikator"]
    actions = ["kontrola_rekapitulacie"]

    def kontrola_rekapitulacie(self, request, queryset):
        def zapisat_riadok(ws, fw, riadok, polozky, header=False):
            for cc, value in enumerate(polozky):
                ws.cell(row=riadok, column = cc+1).value = value 
                if isinstance(value, date):
                    ws.cell(row=riadok, column=cc+1).value = value
                    ws.cell(row=riadok, column=cc+1).number_format = "DD-MM-YYYY"
                    if not cc in fw: fw[cc] = 0
                    if fw[cc] < 12: fw[cc] = 12 
                elif type(value) == Decimal:
                    ws.cell(row=riadok, column=cc+1).value = value
                    ws.cell(row=riadok, column=cc+1).number_format="0.00"
                    if not cc in fw: fw[cc] = 0
                    if fw[cc] < 12: fw[cc] = 12 
                else:
                    ws.cell(row=riadok, column=cc+1).value = str(value)
                    if not cc in fw: fw[cc] = 0
                    if fw[cc] < len(str(value))+2: fw[cc] = len(str(value))+2
        polozky= {
            "Tarifný plat": ["Tarifný plat spolu", 1 ],
            "Osobný príplatok": ["Osobný príplatok", 1],
            "Príplatok za riadenie": ["Príplatok za riadenie", 1],
            "Dovolenka": ["Dovolenka", 1],
            "Prekážky osobné": [ "Prekážky osobné", 1],
            "DoPC": ["Dohody o pracovnej činnosti", 1],
            "DoVP": ["Dohody o vykonaní práce", 1],
            "Sociálny fond": ["Sociálny fond", 2],
            #"Príspevok na stravu": ["Fin.prísp.na stravu z-teľ", 0],
            "Zdravotné poistné": ["Zdravotné poistné spolu", 2],
            "Sociálne poistné": ["Sociálne poistné spolu", 1],
            "DDS": ["Doplnkové dôchodkové sporenie spolu", 1],
            "Odmeny": ["Odmeny spolu", 0],
            "DPN": ["Náhrada príjmu pri DPN", 1],
            }
        #typy = [PlatovyVymer, DoVP, DoPC, PrispevokNaStravne, PrispevokNaRekreaciu]
        typy = [PlatovyVymer, OdmenaOprava, DoVP, DoPC]
        #Vytvoriť workbook
        file_name = f"KontrolaRekapitulacie-{date.today().isoformat()}"
        wb = Workbook()
        ws_prehlad = wb.active
        ws_prehlad.title = "Prehľad"
        harky={}
        fw ={}  #Šírka poľa
        zapisat_riadok(ws_prehlad, fw, 1, ["Mesiac", "Softip", "Django", "Rozdiel"], header=True) 
        for qn, qs in enumerate(queryset):
            ws = wb.create_sheet(title=qs.identifikator)
            zapisat_riadok(ws, fw, 1, ["Položka", "Softip", "Django", "Rozdiel"], header=True) 
            #datum

            #Načítať dáta z Djanga
            #Dátum pre čerpanie
            datum=date(int(qs.identifikator[:4]), int(qs.identifikator[-2:]), 1)
            cerpanie = {}
            for typ in typy:
                for polozka in typ.objects.filter():
                    data = polozka.cerpanie_rozpoctu(datum)
                    for item in data:
                        identif = item['rekapitulacia']
                        if not identif in cerpanie:
                            cerpanie[identif] = item['suma']
                        else:
                            cerpanie[identif] += item['suma']
                        if 'poznamka' in item:
                            messages.warning(request, format_html(item['poznamka']))

            #Načítať dáta z pdf a vyplniť hárok
            fd=open(qs.subor.path, "rb")
            pdf = PdfFileReader(fd)
            s0 = pdf.getPage(0)
            text = s0.extractText()
            for nn, polozka in enumerate(polozky):
                rr=re.findall(r"%s.*"%polozky[polozka][0], text)
                if rr:
                    rslt = re.findall(r"[\d,\d]+", rr[0])
                    zapisat = [
                        polozka, 
                        round(Decimal(rslt[polozky[polozka][1]].replace(",",".")),2), 
                        cerpanie[polozka] if polozka in cerpanie else "",
                        f"=B{nn+2}+C{nn+2}"
                        ]
                    zapisat_riadok(ws, fw, nn+2, zapisat)
                else:
                    zapisat_riadok(ws, fw, nn+2, [polozka])
            nn+=1
            zapisat_riadok(ws, fw, nn+2, ["Spolu",f"=sum(B2:B{nn+1}",f"=sum(C2:C{nn+1}",f"=sum(D2:D{nn+1}"])
            for cc in fw:
                ws.column_dimensions[get_column_letter(cc+1)].width = fw[cc]
            zapisat_riadok(ws_prehlad, fw, qn+2, [qs.identifikator, f"='{qs.identifikator}'!B{len(polozky)+2}", f"='{qs.identifikator}'!C{len(polozky)+2}", f"='{qs.identifikator}'!D{len(polozky)+2}"])

        #Uložiť a zobraziť 
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={file_name}.xlsx'
        wb.save(response)
        return response
    kontrola_rekapitulacie.short_description = "Porovnať mzdové údaje s platovou rekapituláciou"
    #Oprávnenie na použitie akcie, viazané na 'change'
    kontrola_rekapitulacie.allowed_permissions = ('change',)
