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
from uctovnictvo.models import PlatovyVymer, PravidelnaPlatba, NajomneFaktura, InternyPrevod, Poistovna
from uctovnictvo.models import RozpoctovaPolozka, PlatbaBezPrikazu, Pokladna, PrispevokNaRekreaciu, OdmenaOprava
from uctovnictvo.models import TypDochodku, AnoNie, Zdroj, TypZakazky, EkonomickaKlasifikacia, Zamestnanec
from uctovnictvo.odvody import ZamestnanecOdvody, DohodarOdvody
import re
from import_export.admin import ImportExportModelAdmin
from datetime import date
from collections import defaultdict
from beliana.settings import DDS_PRISPEVOK, SOCFOND_PRISPEVOK, ODVODY_VYNIMKA

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
    list_display = ["cislo", "zrusene", "cislopolozky", "adresat", "typdokumentu", "inout", "datum", "sposob", "naspracovanie", "zaznamvytvoril", "vec_html", "suborposta", "prijalodoslal", "datumvytvorenia"]
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
    exclude = ("odosielatel", "url", "prijalodoslal", "datumvytvorenia", "zaznamvytvoril")

    def get_readonly_fields(self, request, obj=None):
        #quick hack: superuser môže kvôli oprave editovať pole datum_softip
        #nejako podobne implementovať aj pre iné triedy, možno pridať permissions "fix_stuff"
        return [] if request.user.has_perm('uctovnictvo.delete_pokladna') else ["zrusene", "poznamka"]

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
    actions = ['generovat2021', "generovat2022", "generovat2023", export_as_xlsx]
    list_totals = [
            ('suma', Sum)
            ]
    list_filter = (
        ('mesiac', DateRangeFilter),
    )
    #stránkovanie a 'Zobraziť všetko'
    list_per_page = 1000
    list_max_show_all = 100000

    def generovat2021(self, request, queryset):
        self.generovat(request, 2021)
    generovat2021.short_description = f"Generovať prehľad čerpania rozpočtu za 2021"
    generovat2021.allowed_permissions = ('change',)

    def generovat2022(self, request, queryset):
        return self.generovat(request, 2022)
    generovat2022.short_description = f"Generovať prehľad čerpania rozpočtu za 2022"
    generovat2022.allowed_permissions = ('change',)

    def generovat2023(self, request, queryset):
        return self.generovat(request, 2023)
    generovat2023.short_description = f"Generovať prehľad čerpania rozpočtu za 2023"
    generovat2023.allowed_permissions = ('change',)

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
                    ws.cell(row=riadok, column=cc+1).value = value
                    if not cc in fw: fw[cc] = 0
                    if fw[cc] < len(str(value))+2: fw[cc] = len(str(value))+2
    
        #najskôr všetko zmazať
        # Nemazať  "Pomocná položka", potrebujeme
        CerpanieRozpoctu.objects.filter().exclude(polozka="Pomocná položka").delete()

        #Vytvoriť workbook
        file_name = f"Cerpanie_rozpoctu_{rok}-{date.today().isoformat()}"
        wb = Workbook()
        ws_prehlad = wb.active
        ws_prehlad.title = "Prehľad"
        ws_polozky = wb.create_sheet(title="Položky")

        # 1. deň v mesiaci
        md1list = [date(rok, mm+1, 1) for mm in range(12)]
        md1list.append(date(rok+1, 1, 1))

        typyOstatne = [PravidelnaPlatba, PrijataFaktura, PlatbaAutorskaSumar, VytvarnaObjednavkaPlatba, NajomneFaktura, PrispevokNaStravne, RozpoctovaPolozka, PlatbaBezPrikazu, Pokladna, PrispevokNaRekreaciu,InternyPrevod]

        cerpanie_rok = defaultdict(dict)
        polozky_riadok = []
        for zden in md1list[:-1]:    # po mesiacoch
            cerpanie_rok = generovat_mzdove(request, zden)

            for typ in typyOstatne:
                for polozka in typ.objects.filter():
                    data = polozka.cerpanie_rozpoctu(zden)
                    for item in data:
                        if item['nazov'] == "Dotácia":
                            #print(item)
                            #trace()
                            pass
                        identif = f"{item['nazov']} {item['zdroj'].kod} {item['zakazka'].kod} {item['ekoklas'].kod}, {zden}"
                        polozky_riadok.append([item['nazov'], 
                                               item['suma'], 
                                               item['subjekt'] if "subjekt" in item else "", 
                                               item['datum'] if "datum" in item else "", 
                                               item['cislo'], item['zdroj'].kod, 
                                               item['zakazka'].kod, 
                                               item['ekoklas'].kod
                                               ])

                        #Unfinished
                        trace()
                        if not identif in cerpanie_rok:
                            cerpanie_rok[identif] = item
                            cerpanie_rok[identif]['zden'] = zden
                        else:
                            cerpanie_rok[identif]['suma'] += item['suma']
                        if 'poznamka' in  item:
                            messages.warning(request, format_html(item['poznamka']))

        #Obsah poľa polozky_riadok zapísať do hárka Položky
        nazvy = ["Názov", "Suma", "Subjekt", "Dátum", "Číslo", "Zdroj", "Zákazka", "Klasifikácia"]
        fw = {}
        zapisat_riadok(ws_polozky, fw, 1, nazvy, header=True)
        riadok=2
        for priadok in polozky_riadok:
            zapisat_riadok(ws_polozky, fw, 1, priadok)
            riadok+=1
        for cc in fw:
            ws_polozky.column_dimensions[get_column_letter(cc+1)].width = fw[cc]

        # Obsah cerpanie_rok zapísať do databázy a do ws_prehlad
        nazvy = ["Názov", "Mesiac", "Suma", "Zdroj", "Zákazka", "Klasifikácia"]
        fw = {}
        zapisat_riadok(ws_prehlad, fw, 1, nazvy, header=True)
        riadok=2
        # Ak ide o Dotáciu, nepriradiť dátum
        for item in cerpanie_rok:
            cr = CerpanieRozpoctu (
                unikatny = item,
                polozka = cerpanie_rok[item]['nazov'],
                mesiac = None if "Dotácia" in item else cerpanie_rok[item]['zden'],
                suma = cerpanie_rok[item]['suma'],
                zdroj = cerpanie_rok[item]['zdroj'],
                zakazka = cerpanie_rok[item]['zakazka'],
                ekoklas = cerpanie_rok[item]['ekoklas'],
                ).save()
            polozky = [cerpanie_rok[item]['nazov'], 
                       cerpanie_rok[item]['zden'], 
                       cerpanie_rok[item]['suma'], 
                       cerpanie_rok[item]['zdroj'].kod, 
                       cerpanie_rok[item]['zakazka'].kod, 
                       cerpanie_rok[item]['ekoklas'].kod
                       ]
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

    #queryset: zoznam mesiacov, za ktoré treba spraviť rekapituláciu
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
                    ws.cell(row=riadok, column=cc+1).value = value
                    ws.cell(row=riadok, column=cc+1).number_format="0.00"
                    if not cc in fw: fw[cc] = 0
                    if fw[cc] < len(str(value))+2: fw[cc] = len(str(value))+2
        polozky= {
            "Plat tarifný plat": ["Tarifný plat spolu", 1 ],
            "Plat osobný príplatok": ["Osobný príplatok", 1],
            "Plat príplatok za riadenie": ["Príplatok za riadenie", 1],
            "Náhrada mzdy - dovolenka": ["Dovolenka", 1],
            "Náhrada mzdy - osobné prekážky": [ "Prekážky osobné", 1],
            "DoPC odmena": ["Dohody o pracovnej činnosti", 1],
            "DoVP odmena": ["Dohody o vykonaní práce", 1],
            "Sociálny fond": ["Sociálny fond", 2],
            #"Príspevok na stravu": ["Fin.prísp.na stravu z-teľ", 0],
            "Zdravotné poistné": ["Zdravotné poistné spolu", 2],
            "Sociálne poistné": ["Sociálne poistné spolu", 1],
            "DDS príspevok": ["Doplnkové dôchodkové sporenie spolu", 1],
            "Plat odmena": ["Odmeny spolu", 0],
            "Náhrada mzdy - PN": ["Náhrada príjmu pri DPN", 1],
            }
        #Vytvoriť workbook
        file_name = f"KontrolaRekapitulacie-{date.today().isoformat()}"
        wb = Workbook()
        ws_prehlad = wb.active
        ws_prehlad.title = "Prehľad"
        harky={}
        fw ={}  #Šírka poľa
        zapisat_riadok(ws_prehlad, fw, 1, ["Mesiac", "Softip", "Django", "Rozdiel"], header=True) 
        for qn, qs in enumerate(sorted(queryset, key=lambda x: x.identifikator)):  #queryset: zoznam mesiacov, za ktoré treba spraviť rekapituláciu
            ws = wb.create_sheet(title=qs.identifikator)
            zapisat_riadok(ws, fw, 1, ["Položka", "Softip", "Django", "Rozdiel"], header=True) 
            #datum

            #Načítať dáta z Djanga
            #Dátum pre čerpanie
            datum=date(int(qs.identifikator[:4]), int(qs.identifikator[-2:]), 1)
            cerpanie = generovat_mzdove(request, datum)

            #Spočítať po typoch
            sumarne={}
            for item in cerpanie:
                sumarne[item['nazov']] = Decimal(sumarne[item['nazov']]) + Decimal(item['suma']) if item['nazov'] in sumarne else item['suma']
                pass

            #Načítať dáta z pdf a vyplniť hárok
            fd=open(qs.subor.path, "rb")
            pdf = PdfFileReader(fd)
            s0 = pdf.getPage(0)
            pdftext = s0.extractText()
            for nn, polozka in enumerate(polozky):
                rr=re.findall(r"%s.*"%polozky[polozka][0], pdftext)
                if rr:
                    rslt = re.findall(r"[\d,\d]+", rr[0])
                    zapisat = [
                        polozka, 
                        round(Decimal(rslt[polozky[polozka][1]].replace(",",".")),2), 
                        round(Decimal(sumarne[polozka]),2) if polozka in sumarne else 0,
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

# Generovať sumáre mzdové položky
def generovat_mzdove(request, zden):
    #Po osobách (zamestnanci a dohodári) vytvoriť zoznam všetkých relevantných položiek
    po_osobach = defaultdict(list)
    for typ in [PlatovyVymer, OdmenaOprava, DoPC, DoVP, DoBPS]:
        for polozka in typ.objects.filter():
            data = polozka.cerpanie_rozpoctu(zden)
            if not data: continue   #netýka sa akuálneho mesiaca
            for item in data:
                po_osobach[item['subjekt']].append(item)
                if 'poznamka' in  item:
                    messages.warning(request, format_html(item['poznamka']))

    #Položky, ktoré sa počítajú z celkového príjmu
    #Položky, ktoré definujú položky pre výpočet vymeriavacích základov
    vymer_odmena = ["Plat tarifný plat", "Plat osobný príplatok", "Plat príplatok za riadenie", "Plat odmena"]
    nahrady = ["Náhrada mzdy - osobné prekážky", "Náhrada mzdy - dovolenka", "Náhrada mzdy - PN"]

    polozky_socfond =       vymer_odmena
    polozky_dds =           vymer_odmena + ["Plat odchodné", "Plat odstupné"]
    polozky_soczdrav_zam =  vymer_odmena + ["Náhrada mzdy - osobné prekážky", "Náhrada mzdy - dovolenka", "Plat odchodné", "Plat odstupné"]
    polozky_soczdrav_dovp = ["DoVP odmena"]
    polozky_soczdrav_dopc = ["DoPC odmena"]
    polozka_vylucitelnost = ["Plat tarifný plat"]   #0 znamená, že zamestnane celý mesiac nepracoval, teda bol vylúčiteľný (bol na PN)

    cerpanie = []   #zoznam poloziel cerpania
    for meno in po_osobach:
        #celková odmena
        osoba = po_osobach[meno][0]['osoba']
        zaklad_dds = 0
        zaklad_socfond = 0
        zaklad_soczdrav_zam = 0
        zaklad_soczdrav_dovp = 0
        zaklad_soczdrav_dopc = 0
        zaklad_vylucitelnost = 0
        dohoda_vynimka = AnoNie.NIE
        #Vytvoriť čiastočný zoznam položiek čerpania s položkami, ktoré sa prenášajú priamo a vypočítať sumáre na výpočet ostatných
        for item in po_osobach[meno]:
            cerpanie.append(item)
            if item['nazov'] in polozka_vylucitelnost:
                zaklad_vylucitelnost += item['suma']
            if item['nazov'] in polozky_dds:
                zaklad_dds += item['suma']
            if item['nazov'] in polozky_socfond:
                zaklad_socfond += item['suma']
            if item['nazov'] in polozky_soczdrav_zam:
                zaklad_soczdrav_zam += item['suma']
            if item['nazov'] in polozky_soczdrav_dovp:
                zaklad_soczdrav_dovp += item['suma']
                dohoda_vynimka = AnoNie.ANO if item['vynimka'] == AnoNie.ANO else dohoda_vynimka    #pre prípad, že má dohodár, ktorý si uplatňuje výnimku, viac dohôd
            if item['nazov'] in polozky_soczdrav_dopc:
                zaklad_soczdrav_dopc += item['suma']
                dohoda_vynimka = AnoNie.ANO if item['vynimka'] == AnoNie.ANO else dohoda_vynimka    #pre prípad, že má dohodár, ktorý si uplatňuje výnimku, viac dohôd

        #Výpočet položiek, ktoré sa rátajú zo sumárnych hodnôt
        if type(osoba) == Zamestnanec and osoba.dds == AnoNie.ANO:
            if not osoba.dds_od:
                messages.warning(request, f"Vypočítaná suma výšky príspevku do DDS je nesprávna. V údajoch zamestnanca '{osoba}' treba vyplniť pole 'DDS od'")
            else: # Príspevok do DDS sa vypláca od 1. dňa mesiaca, keď bola uzatvorena dohoda
                dds_od = date(osoba.dds_od.year, osoba.dds_od.month, 1)
            if zden >= dds_od:
                cerpanie = cerpanie + gen_dds(osoba, zaklad_dds, zden, PlatovyVymer.td_konv(osoba))
        cerpanie = cerpanie + gen_socfond(osoba, zaklad_socfond, zden)
        vylucitelnost = False if zaklad_vylucitelnost else True
        cerpanie = cerpanie + gen_soczdrav(osoba, "plat", zaklad_soczdrav_zam, zden, PlatovyVymer.td_konv(osoba), vylucitelnost=vylucitelnost)
        cerpanie = cerpanie + gen_soczdrav(osoba, "dovp", zaklad_soczdrav_dovp, zden, DoVP.td_konv(osoba), vynimka=dohoda_vynimka)
        cerpanie = cerpanie + gen_soczdrav(osoba, "dopc", zaklad_soczdrav_dopc, zden, DoPC.td_konv(osoba), vynimka=dohoda_vynimka)
    return cerpanie

#Generovať položky pre socialne a zdravotne poistenie
def gen_soczdrav(osoba, typ, suma, zden, td_konv, vynimka=AnoNie.NIE, vylucitelnost=False):
    zdroj, zakazka = get_zdroj_zakazka(zden)
    subjekt = f"{osoba.priezvisko}, {osoba.meno}, (za {zden.year}/{zden.month})"
    if typ == "plat":
        socpoist, _, zdravpoist, _ = ZamestnanecOdvody(-float(suma), td_konv, zden, vylucitelnost)
    else:
        socpoist, _, zdravpoist, _ = DohodarOdvody(-float(suma), td_konv, zden, ODVODY_VYNIMKA if vynimka == AnoNie.ANO else 0)
    poistne=[]
    for item in socpoist:
        soc = {
            "nazov": f"Sociálne poistné",
            "suma": -round(Decimal(socpoist[item]),2),
            "zdroj": zdroj,
            "zakazka": zakazka,
            "datum": zden,
            "subjekt": subjekt,
            "cislo": "-",
            "ekoklas": item
        }
        poistne.append(soc)
    ekoklas = "621" if osoba.poistovna == Poistovna.VSZP else "623"
    #Vytvoriť položku pre DDS - zdravotné
    zdrav = {
        "nazov": f"Zdravotné poistné",
        "suma": -Decimal(zdravpoist['zdravotne']),
        "zdroj": zdroj,
        "zakazka": zakazka,
        "datum": zden,
        "subjekt": subjekt,
        "cislo": "-",
        "ekoklas": EkonomickaKlasifikacia.objects.get(kod=ekoklas)
        }
    poistne.append(zdrav)
    pass
    return poistne

#Generovať položky pre DDS
def gen_dds(zamestnanec, suma, zden, td_konv):
    zdroj, zakazka = get_zdroj_zakazka(zden)
    subjekt = f"{zamestnanec.priezvisko}, {zamestnanec.meno}, (za {zden.year}/{zden.month})"

    #Vytvoriť položku pre DDS
    suma = DDS_PRISPEVOK*float(suma)/100
    dds = {
        "nazov": "DDS príspevok",
        "suma": round(Decimal(suma),2),
        "zdroj": zdroj,
        "zakazka": zakazka,
        "datum": zden,
        "subjekt": subjekt,
        "cislo": "-",
        "ekoklas": EkonomickaKlasifikacia.objects.get(kod="637016")
        }
    _, _, zdravpoist, _ = ZamestnanecOdvody(suma, td_konv, zden)
    ekoklas = "621" if zamestnanec.poistovna == Poistovna.VSZP else "623"
    #Vytvoriť položku pre DDS - zdravotné
    dds_zdrav = {
        "nazov": "Zdravotné poistné",   #zdravotné poustné nemá strop, takže môžeme riešiť takto
        "suma": zdravpoist['zdravotne'],
        "zdroj": zdroj,
        "zakazka": zakazka,
        "datum": zden,
        "subjekt": subjekt,
        "cislo": "-",
        "ekoklas": EkonomickaKlasifikacia.objects.get(kod=ekoklas)
        }
    return [dds, dds_zdrav]


#Generovať položky pre socialny fond
def gen_socfond(zamestnanec, suma, zden):
    zdroj, zakazka = get_zdroj_zakazka(zden)
    subjekt = f"{zamestnanec.priezvisko}, {zamestnanec.meno}, (za {zden.year}/{zden.month})"
    suma = SOCFOND_PRISPEVOK*float(suma)/100
    socfond = {
        "nazov": "Sociálny fond",
        "rekapitulacia": "Sociálny fond",
        "suma": round(Decimal(suma),2),
        "zdroj": zdroj,
        "zakazka": zakazka,
        "datum": zden if zden < date.today() else None,
        "subjekt": subjekt,
        "cislo": "-",
        "ekoklas": EkonomickaKlasifikacia.objects.get(kod="637016")
        }
    return [socfond]
 
def get_zdroj_zakazka(zden):
    if zden in [date(2022,1,1), date(2022,2,1)]:   #Počas tychto 3 mesiacov bolo všetko inak :D
        zdroj = Zdroj.objects.get(kod="131L") 
        zakazka = TypZakazky.objects.get(kod="131L0001")
    else:
        zdroj = Zdroj.objects.get(kod="111") 
        zakazka = TypZakazky.objects.get(kod="11010001 spol. zák.")
    return zdroj, zakazka
