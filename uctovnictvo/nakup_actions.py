#Akcie pre Objednávka
import os, locale
from ipdb import set_trace as trace

from django.conf import settings
from django.contrib import messages
from .models import SystemovySubor, AnoNie, Objednavka, rozdelit_polozky, FormaUhrady

from openpyxl import load_workbook
from openpyxl.workbook.workbook import Workbook
from openpyxl.styles import Font, Color, colors, Alignment, PatternFill , numbers
from openpyxl.utils import get_column_letter
from openpyxl.styles import Border, Side, PatternFill, Font, GradientFill, Alignment
from decimal import Decimal
from datetime import date

# lokálna funkcia, nemá zmysel ju volať zvonka
def VyplnitHarok(ws_obj, objednavka, je_vyplatenie):
    prvy_riadok = 12 #prvy riadok tabulky
    pocet_riadkov = 8 # pri zmene zmeniť aj models.Objednavka.clean.pocet_riadkov

    ziadatel = objednavka.ziadatel if objednavka.ziadatel else objednavka.vybavuje
    vybavuje = objednavka.vybavuje
    today = date.today().strftime("%d.%m.%Y")

    if je_vyplatenie:
        ws_obj["A1"].value = f"ŽIADOSŤ č. {objednavka.cislo}"
        ws_obj["A2"].value = "o preplatenie nákladov za obstaranie tovarov, služieb a stavebných prác formou drobného nákupu"
        ws_obj["A5"].value = vybavuje.menopriezvisko(True)
        ws_obj["C25"].value = objednavka.vybavuje.bankovy_kontakt
        ws_obj["A33"].value = "Súhlasím s preplatením nákladov na obstaranie tovarov / služieb / stavebných prác podľa zoznamu"
    else:
        ws_obj["A1"].value = f"ŽIADANKA č. {objednavka.cislo}"
        ws_obj["A2"].value = "na obstaranie tovarov, služieb a stavebných prác formou drobného nákupu"
        ws_obj["L4"].value = today
        ws_obj["C25"].value = ""
        ws_obj["A5"].value = ziadatel.menopriezvisko(True)

    ws_obj["G8"].value = objednavka.popis
    ws_obj["D22"].value = vybavuje.menopriezvisko(True)
    ws_obj["C24"].value = vybavuje.menopriezvisko(True)
    ws_obj["B30"].value = objednavka.zdroj.kod
    ws_obj["H30"].value = objednavka.zakazka.kod
    if objednavka.forma_uhrady == FormaUhrady.UCET:
        ws_obj["A27"].value = "x"
    else:
        ws_obj["A28"].value = "x"

    #položky
    objednane = objednavka.objednane_polozky.split("\n")
    for rr, polozka in enumerate(objednane):
        riadok = prvy_riadok+rr
        prvky = rozdelit_polozky(polozka)

        nr =  int(1+len(prvky[0])/35)
        if nr > 1: ws_obj.row_dimensions[riadok].height = 15 * nr
        ws_obj.cell(row=riadok, column=1).value = rr+1
        ws_obj.cell(row=riadok, column=2).value = prvky[0]
        val = float(prvky[1].strip().replace(",","."))
        ws_obj.cell(row=riadok, column=10).value = val
        ws_obj.cell(row=riadok, column=10).number_format= "0.00"
        ws_obj.cell(row=riadok, column=12).value = prvky[2]
        if len(prvky) == 4:
            ws_obj.cell(row=riadok, column=14).value = prvky[3]
        #
    return ws_obj, prvy_riadok, pocet_riadkov

# lokálna funkcia, nemá zmysel ju volať zvonka
def OtvoritSablonuNakupu():
    #úvodné testy
    objednavky_dir_path  = os.path.join(settings.MEDIA_ROOT,settings.POKLADNA_DIR)
    if not os.path.isdir(objednavky_dir_path):
        os.makedirs(objednavky_dir_path)
    
    #Načítať súbor šablóny
    nazov_objektu = "Šablóna žiadanka /žiadosť nákup"  #Presne takto musí byť objekt pomenovaný
    sablona = SystemovySubor.objects.filter(subor_nazov = nazov_objektu)
    if not sablona:
        return messages.ERROR, f"V systéme nie je definovaný súbor '{nazov_objektu}'.", None
    nazov_suboru = sablona[0].subor.file.name 
    workbook = load_workbook(filename=nazov_suboru)
    return workbook

def VytvoritSuborObjednavky(objednavka):
    if not objednavka.dodavatel:
        return messages.ERROR, f"Pole Dodávateľ v objednávke {objednavka.cislo} nie je vyplnené. Súbor objednávky nebol vygenerovaný.", None
    workbook = OtvoritSablonuObjednavky()
    if type(workbook) != Workbook:
        return workbook #Error

    ws_obj, prvy_riadok, pocet_riadkov = VyplnitHarok(workbook["Objednávka"], objednavka, True)

    if objednavka.termin_dodania:
        ws_obj[f"A{prvy_riadok+pocet_riadkov+2}"].value = ws_obj[f"A{prvy_riadok+pocet_riadkov+2}"].value.replace("[[termin_dodania]]", objednavka.termin_dodania)
    else:
        ws_obj[f"A{prvy_riadok+pocet_riadkov+2}"].value = ws_obj[f"A{prvy_riadok+pocet_riadkov+2}"].value.replace("[[termin_dodania]]", "")
    if not objednavka.datum_vytvorenia:
        return messages.ERROR, "Vytváranie súboru objednávky zlyhalo, lebo objednávka nemá zadaný dátum vytvorenia.", None
    ws_obj[f"A{prvy_riadok+pocet_riadkov+4}"].value = ws_obj[f"A{prvy_riadok+pocet_riadkov+4}"].value.replace("[[datum]]", objednavka.datum_vytvorenia.strftime("%d. %m. %Y"))
  
    ws_kl = workbook["Finančná kontrola objednávka"]
    ws_kl["A1"].value = ws_kl["A1"].value.replace("[[cislo]]", objednavka.cislo)
    ws_kl["A1"].value = ws_kl["A1"].value.replace("[[datum]]", objednavka.datum_vytvorenia.strftime("%d. %m. %Y"))

    #uložiť
    workbook.remove_sheet(workbook.get_sheet_by_name("Žiadanka"))
    workbook.remove_sheet(workbook.get_sheet_by_name("Finančná kontrola žiadanka"))
    #Create directory admin.rs_login if necessary
    nazov = f'{objednavka.cislo}-{objednavka.dodavatel.nazov.replace(" ","").replace(".","").replace(",","-")}.xlsx'
    opath = os.path.join(settings.OBJEDNAVKY_DIR,nazov)
    workbook.save(os.path.join(settings.MEDIA_ROOT,opath))
    return messages.SUCCESS, f"Súbor objednávky {objednavka.cislo} bol úspešne vytvorený ({opath}).", opath

def VytvoritSuborZiadanky(objednavka):
    workbook = OtvoritSablonuNakupu()
    if type(workbook) != Workbook:
        return workbook #Error

    ws_obj, prvy_riadok, pocet_riadkov = VyplnitHarok(workbook["Žiadanka - žiadosť"], objednavka, False)

    ws_kl = workbook["Krycí list"]
    ws_kl["A1"].value = ws_kl["A1"].value.replace("[[cislo]]", objednavka.cislo[2:])

    #uložiť
    nazov = f'{objednavka.cislo[2:]}-ziadanka.xlsx'
    opath = os.path.join(settings.POKLADNA_DIR,nazov)
    workbook.save(os.path.join(settings.MEDIA_ROOT,opath))
    return messages.SUCCESS, f"Súbor žiadanky {objednavka.cislo[2:]} bol úspešne vytvorený ({opath}).", opath

def VytvoritSuborPreplatenie(objednavka):
    workbook = OtvoritSablonuNakupu()
    if type(workbook) != Workbook:
        return workbook #Error

    ws_obj, prvy_riadok, pocet_riadkov = VyplnitHarok(workbook["Žiadanka - žiadosť"], objednavka, True)

    ws_kl = workbook["Krycí list"]
    ws_kl["A2"].value = ws_kl["A2"].value.replace("[[cislo]]", objednavka.cislo[2:])

    #uložiť
    nazov = f'{objednavka.cislo[2:]}-vyplatenie.xlsx'
    opath = os.path.join(settings.POKLADNA_DIR,nazov)
    workbook.save(os.path.join(settings.MEDIA_ROOT,opath))
    return messages.SUCCESS, f"Súbor žiadosti {objednavka.cislo[2:]} o vyplatenie bol úspešne vytvorený ({opath}).", opath
