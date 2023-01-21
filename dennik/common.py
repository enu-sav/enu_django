
import os, csv, re, locale
from datetime import date, datetime
from decimal import Decimal
from collections import defaultdict
from django.conf import settings
from django.contrib import messages
from django.db.models.fields.files import FieldFile
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, Color, colors, Alignment, PatternFill , numbers
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.pagebreak import Break
from ipdb import set_trace as trace
from .models import Formular, TypFormulara
from zmluvy.models import PlatbaAutorskaOdmena, AnoNie

#Dodatočné tokeny, doplňované z databázy alebo inak
#typ dokumentu VSEOBECNY
polia_vseob = {
        "dat_vytv": "Dátum vytvorenia dokumentu."
        }

def isEmpty(values):
    empty = True
    for vv in values:
        if vv: return False
    return True

def locale_format(d):
    return locale.format('%.2f', d, grouping=True)

def VyplnitAVygenerovat(formular):
    #testy
    try:
        with open(formular.sablona.file.name, "r") as f:
            sablona = f.read()
    except:
        return messages.ERROR, f"Súbor šablóny {formular.sablona} neexistuje alebo je nečitateľný.", None, None

    try:
        with open(formular.data.file.name, "r") as f:
            workbook = load_workbook(filename=formular.data)
    except:
        return messages.ERROR, f"Dátový súbor {formular.data} neexistuje alebo je nečitateľný.", None, None
    ws = workbook.active

    #hlavička, po prvú prázdnu bunku
    hdr = {}
    col_range = ws[ws.min_column : ws.max_column]
    for n in range(1,1024):
        val = ws.cell(1,n).value
        if not val:
            break
        else:
            hdr[val] = n

    if formular.typformulara == TypFormulara.VSEOBECNY:
        return VyplnitAVygenerovatVseobecny(formular, sablona, ws, hdr)
    elif formular.typformulara == TypFormulara.AH_ZRAZENA:
        return VyplnitAVygenerovatAHZrazena(formular, sablona, ws, hdr)
    else:
        return messages.ERROR, f"Typ formulára {formular.typformulara} zatiaľ nie je implementovaný.", None, None

def VyplnitAVygenerovatVseobecny(formular, sablona, iws, hdr):

    #testy
    stokens = re.findall(r"\[\[(.*)\]\]",sablona)   #tokeny v šablóne
    chybajuce = []
    for stoken in stokens:
        if not stoken in hdr.keys():
            chybajuce.append(stoken)
    #doplniť testy pre zmluvy, dohodarov a zamestnancov
    # ak dat_vytv nie je určený, použijeme today()
    if "dat_vytv" in chybajuce:
        chybajuce = chybajuce.remove("dat_vytv")
    if chybajuce:
        return messages.ERROR, f"V dátovom súbore chýbajú stĺpce pre tokeny: '{', '.join(chybajuce)}'. Skontrolujte preklepy alebo doplňte stĺpce. Dáta sa načítavajú po prvý stĺpec s prázdnou hlavičkou.", None, None

    #vyplniť polia
    locale.setlocale(locale.LC_ALL, 'sk_SK.UTF-8')
    text = re.findall(r"<office:text[^>]*>(.*)</office:text>", sablona, re.DOTALL)[0]
    #najskor vymazat text dokumentu
    sablona = sablona.replace(text, "")
    nn = 0
    for row in iws.rows:
        values = [c.value for c in row]
        #Preskočiť 1. riadok
        if nn == 0:
            nn += 1
            continue
        #Skončiť na 1. prázdnom riadku
        if isEmpty(values): break
        #Kopírovať 'text')
        atext = (text + '.')[:-1]
        for key, cell in zip(hdr, row):
            if key[:2].lower() == "n_":
                atext = atext.replace(f"[[{key}]]", "" if cell.value==None else locale_format(cell.value))
            else:
                atext = atext.replace(f"[[{key}]]", str(cell.value) if cell.value else "")
        if formular.typformulara == TypFormulara.VSEOBECNY:
            for key in polia_vseob:
                if key == "dat_vytv":
                    atext = atext.replace(f"[[{key}]]", date.today().strftime("%-d. %-m. %Y"))
        #Pridať ako nový text na koniec existujúceho textu
        sablona = sablona.replace("</office:text>",f"{atext}\n</office:text>")
        nn += 1

    #Uložiť súbory
    o_text = f"{formular}.fodt"
    with open(os.path.join(settings.MEDIA_ROOT,settings.FORM_DIR_NAME,o_text), "w") as f:
        f.write(sablona)

    #status, msg, vyplnene, vyplnene_data
    return messages.SUCCESS, f"Vytvorený bol súbor '{o_text}' s {nn} vyplnenými dokumentami", os.path.join(settings.FORM_DIR_NAME,o_text), formular.data.name

def VyplnitAVygenerovatAHZrazena(formular, sablona, iws, hdr):

    #vyplniť polia
    locale.setlocale(locale.LC_ALL, 'sk_SK.UTF-8')
    stext = re.findall(r"<office:text[^>]*>(.*)</office:text>", sablona, re.DOTALL)[0]
    #najskor vymazat text dokumentu
    sablona = sablona.replace(stext, "")
    # nahradiť globálne hodnoty z dátového súboru
    if "za_rok" in hdr:
        za_rok = iws.cell(row=2, column=hdr["za_rok"]).value
        stext.replace("[[za_rok]]", str(za_rok))
    else:
        return messages.ERROR, f"V dátovom súbore chýbajú stĺpec pre token 'za_rok'", None, None
    if "dat_vytv" in hdr:
        dat_vytv = iws.cell(row=2, column=hdr["dat_vytv"]).value.strftime("%-d. %-m. %Y")
        stext.replace("[[dat_vytv]]", dat_vytv)
    nn = 0

    #Sčítať vyplatené odmeny autorov za daný rok
    autori = defaultdict(dict)
    platby = PlatbaAutorskaOdmena.objects.filter(cislo__startswith=f"AH-{za_rok}")
    nn = 2
    for platba in platby:
        login = platba.autor.rs_login
        mp = f"{platba.autor.meno} {platba.autor.priezvisko}"
        if platba.autor.titul_pred_menom:
            mp = f"{platba.autor.titul_pred_menom} {mp}"
        if platba.autor.titul_za_menom:
            mp = f"{mp}, {platba.autor.titul_za_menom}"
        if not login in autori:
            autori[login]["login"] = login                            # stĺpec A
            autori[login]["email"] = platba.autor.email
            autori[login]["meno"] = mp
            autori[login]["rodne_cislo"] = platba.autor.rodne_cislo
            autori[login]["adresa_ulica"] = platba.autor.adresa_ulica
            autori[login]["adresa_mesto"] = platba.autor.adresa_mesto
            autori[login]["adresa_stat"] = platba.autor.adresa_stat
            autori[login]["koresp_adresa_institucia"] = platba.autor.koresp_adresa_institucia
            autori[login]["koresp_adresa_ulica"] = platba.autor.koresp_adresa_ulica
            autori[login]["koresp_adresa_mesto"] = platba.autor.koresp_adresa_mesto
            autori[login]["koresp_adresa_stat"] = platba.autor.koresp_adresa_stat
            autori[login]["obdobie"] = ""
            autori[login]["nevyplacat"] = platba.autor.nevyplacat
            autori[login]["datum_dohoda_podpis"] = platba.autor.datum_dohoda_podpis
            autori[login]["datum_dohoda_oznamenie"] = platba.autor.datum_dohoda_oznamenie
            autori[login]["dohodasubor"] = platba.autor.dohodasubor
            autori[login]["rezident"] = platba.autor.rezident           #Q
            autori[login]["zdanit"] = platba.autor.zdanit               #R
            autori[login]["zhonor"] = 0
            autori[login]["zfond"] = 0
            autori[login]["z_dane"] = 0                                 #T
            autori[login]["dan"] = 0                                    #U
            autori[login]["zvypl"] = 0                                  #V
            autori[login]["nhonor"] = 0
            autori[login]["nfond"] = 0
            autori[login]["nvypl"] = 0
            autori[login]["T1"] = f'=OR(Q{nn}="nie";R{nn}="nie")'    #AA
            autori[login]["T2"] = f'=U{nn}=0'                           #AB
            autori[login]["Test"] = f'=AA{nn}=AB{nn}'                   #AC
            nn += 1
        autori[login]["obdobie"] += f"{platba.cislo} "
        if platba.odvedena_dan:
            autori[login]["zhonor"] += platba.honorar
            autori[login]["zfond"] += platba.odvod_LF
            #Chyba v originali
            #autori[login]["z_dane"] += platba.honorar - platba.odvod_LF - platba.odvedena_dan
            autori[login]["z_dane"] += platba.honorar - platba.odvod_LF
            autori[login]["dan"] += platba.odvedena_dan
            autori[login]["zvypl"] += platba.uhradena_suma
        else:
            autori[login]["nhonor"] += platba.honorar
            autori[login]["nfond"] += platba.odvod_LF
            autori[login]["nvypl"] += platba.uhradena_suma
    poautoroch = "PoAutoroch" 

    #uložiť do xlsx súboru
    owb = Workbook()
    ows = owb.active
    ows.append(list(autori[login].keys()))
    nn=1
    for autor in autori:
        print(nn,autor)
        values = []
        for val in autori[autor].values():
            if not val:
                values.append("")
            elif type(val) == str:
                values.append(val)
            elif type(val) == Decimal:
                values.append(locale_format(val))
            elif type(val) == date:
                values.append(val.strftime('%-d. %-m. %Y'))
            elif type(val)==FieldFile:
                values.append(str(val))
            else:
                values.append(val)
            #values = [str(val).replace("None","") if type(val)==str else val for val in autori[autor].values()]
        ows.append(values)
        nn+=1

    # Vytvoriť potvrdenia
    for login in autori:
        text = "%s"%stext
        #zapísať hodnoty
        text =text.replace("[[meno]]",autori[login]['meno'])
        adr = ["","","",""]
        adrr=0  #riadok adresy
        if autori[login]["koresp_adresa_mesto"]:
            if autori[login]["koresp_adresa_ulica"]:
                adr[adrr] = autori[login]["koresp_adresa_ulica"]
                adrr += 1
            if autori[login]["koresp_adresa_institucia"]:
                adr[adrr] = autori[login]["koresp_adresa_institucia"]
                adrr += 1
            if autori[login]["koresp_adresa_mesto"]:
                adr[adrr] = autori[login]["koresp_adresa_mesto"]
                adrr += 1
            if autori[login]["koresp_adresa_stat"]:
                adr[adrr] = autori[login]["koresp_adresa_stat"]
                adrr += 1
        else:
            if autori[login]["adresa_ulica"]:
                adr[adrr] = autori[login]["adresa_ulica"]
                adrr += 1
            if autori[login]["adresa_mesto"]:
                adr[adrr] = autori[login]["adresa_mesto"]
                adrr += 1
            if autori[login]["adresa_stat"]:
                adr[adrr] = autori[login]["adresa_stat"]
                adrr += 1
        adrs = ["[[adr1]]","[[adr2]]","[[adr3]]","[[adr4]]"]
        for a,s in zip(adr, adrs):
            text = text.replace(s,a)

        #adresa
        addr = f"{autori[login]['adresa_mesto']}, {autori[login]['adresa_stat']}"
        if autori[login]["adresa_ulica"]:
            addr = f"{autori[login]['adresa_ulica']}, {addr}"
        text = text.replace("[[atp]]", addr)
        text = text.replace("[[rc]]", autori[login]["rodne_cislo"])

        text = text.replace("[[zhonor]]", str(autori[login]["zhonor"]).replace(".",","))
        text = text.replace("[[zfond]]", str(autori[login]["zfond"]).replace(".",","))
        text = text.replace("[[z_dane]]", str(autori[login]["z_dane"]).replace(".",","))
        text = text.replace("[[dan]]", str(autori[login]["dan"]).replace(".",","))
        text = text.replace("[[zvypl]]", str(autori[login]["zvypl"]).replace(".",","))

        text = text.replace("[[nhonor]]", str(autori[login]["nhonor"]).replace(".",","))
        text = text.replace("[[nfond]]", str(autori[login]["nfond"]).replace(".",","))
        text = text.replace("[[nvypl]]", str(autori[login]["nvypl"]).replace(".",","))
        text = text.replace("[[datum]]", datetime.today().strftime('%-d. %-m. %Y'))
        text = text.replace("[[obd]]", str(za_rok))

        #Dôvod nezdanenia
        dovod=""
        if autori[login]["rezident"] == AnoNie.NIE and not autori[login]["dan"]:
            text = text.replace("[[nezdanenezaklad]]", f"na základe Zmluvy medzi Slovenskou republikou a štátom daňovej rezidencie autora o zamedzení dvojitého zdanenia")
            dovod="R"
        elif autori[login]["zdanit"] == AnoNie.NIE and not autori[login]["dan"]:
            dp = autori[login]['datum_dohoda_podpis'].strftime('%-d. %-m. %Y')
            text = text.replace("[[nezdanenezaklad]]", f"na základe dohody medzi EnÚ a autorom podľa § 43 ods. 14 Zákona o dani z príjmov podpísanej dňa {dp}")
            dovod="D"
        else:
            text = text.replace("[[nezdanenezaklad]]", "")
            dovod="X"
        sablona = sablona.replace("</office:text>",f"{text}\n</office:text>")

    #Uložiť súbory
    o_text = f"{formular}.fodt"
    with open(os.path.join(settings.MEDIA_ROOT,settings.FORM_DIR_NAME,o_text), "w") as f:
        f.write(sablona)
    o_data = f"{formular}.xlsx"
    owb.save(os.path.join(settings.MEDIA_ROOT,settings.FORM_DIR_NAME,o_data))

    #status, msg, vyplnene, vyplnene_data
    return messages.SUCCESS, f"Vytvorený bol súbor '{o_text}' s {len(autori)} vyplnenými dokumentami", os.path.join(settings.FORM_DIR_NAME,o_text), os.path.join(settings.FORM_DIR_NAME,o_data)
