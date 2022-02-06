
import os, csv, re, locale
from datetime import date, datetime
from django.conf import settings
from django.contrib import messages
from openpyxl import load_workbook
from openpyxl.styles import Font, Color, colors, Alignment, PatternFill , numbers
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.pagebreak import Break
from ipdb import set_trace as trace
from .models import Formular, TypFormulara

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
    nazov_suboru=formular.sablona.file.name
    try:
        #with open(settings.AUTHORS_CONTRACT_TEMPLATE, "r") as f:
        with open(nazov_suboru, "r") as f:
            sablona = f.read()
    except:
        return messages.ERROR, f"Súbor šablóny {formular.sablona} neexistuje alebo je nečitateľný.", None, None

    workbook = load_workbook(filename=formular.data)
    iws = workbook.active

    #hlavička, po prvú prázdnu bunku
    hdr = []
    col_range = iws[iws.min_column : iws.max_column]
    for n in range(1,1024):
        val = iws.cell(1,n).value
        if not val:
            break
        else:
            hdr.append(val)

    #testy
    stokens = re.findall(r"\[\[(.*)\]\]",sablona)   #tokeny v šablóne
    chybajuce = []
    for stoken in stokens:
        if not stoken in hdr:
            chybajuce.append(stoken)
    #doplniť testy pre zmluvy, dohodarov a zamestnancov
    # ak dat_vytv nie je určený, použilene today()
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
        if values[0] == hdr[0] and values[1] == hdr[1]:
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
                    atext = atext.replace(f"[[{key}]]", date.today().strftime("%d. %m. %Y"))
        #Pridať ako nový text na koniec existujúceho textu
        sablona = sablona.replace("</office:text>",f"{atext}\n</office:text>")
        nn += 1

    #Uložiť súbory
    o_text = f"{formular}.fodt"
    with open(os.path.join(settings.MEDIA_ROOT,settings.FORM_DIR_NAME,o_text), "w") as f:
        f.write(sablona)

    #status, msg, vyplnene, vyplnene_data
    return messages.SUCCESS, f"Vytvorený bol súbor '{o_text}' s {nn} vyplnenými dokumentami", os.path.join(settings.FORM_DIR_NAME,o_text), formular.data.name
