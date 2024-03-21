#Akcie pre Objednávka
import os, locale
from ipdb import set_trace as trace

from django.conf import settings
from django.contrib import messages
from .models import SystemovySubor, AnoNie, Objednavka

from openpyxl import load_workbook
from openpyxl.workbook.workbook import Workbook
from openpyxl.styles import Font, Color, colors, Alignment, PatternFill , numbers
from openpyxl.utils import get_column_letter
from openpyxl.styles import Border, Side, PatternFill, Font, GradientFill, Alignment
from decimal import Decimal

# lokálna funkcia, nemá zmysel ju volať zvonka
def VyplnitHarok(ws_obj, objednavka, je_objednavka):
    prvy_riadok = 15 #prvy riadok tabulky
    pocet_riadkov = 12 # pri zmene zmeniť aj models.Objednavka.clean.pocet_riadkov
    dph = 1+settings.DPH/100

    ws_obj["A3"].value = ws_obj["A3"].value.replace("[[cislo]]",objednavka.cislo[2:])
    if je_objednavka:
        ws_obj["B6"].value = objednavka.vybavuje2.osoba.menopriezvisko(True)
        if  objednavka.vybavuje2.telefon:
            ws_obj["B7"].value = objednavka.vybavuje2.telefon
        ws_obj["B9"].value = objednavka.vybavuje2.enu_email
    else:
        if objednavka.ziadatel:
            ws_obj["B6"].value = objednavka.ziadatel.menopriezvisko(True)
            ws_obj["B9"].value = objednavka.ziadatel.email
        else:
            ws_obj["B6"].value = objednavka.vybavuje2.osoba.menopriezvisko(True)
            ws_obj["B9"].value = objednavka.vybavuje2.enu_email
    #dodávateľ
    if objednavka.dodavatel:
        ws_obj["D6"].value = objednavka.dodavatel.nazov
        ws_obj["D7"].value = objednavka.dodavatel.adresa_ulica
        ws_obj["D8"].value = objednavka.dodavatel.adresa_mesto
        ws_obj["D9"].value = objednavka.dodavatel.adresa_stat

    #položky
    add_sum = True  # či s má do posledného riadka vložiť súčet
    objednane = objednavka.objednane_polozky.split("\n")
    for rr, polozka in enumerate(objednane):
        riadok = prvy_riadok+rr
        prvky = polozka.split(";")
        if len(prvky) == 2:  #zlúčiť bunky
            ws_obj.merge_cells(f'B{riadok}:E{riadok}')
            nr =  int(1+len(prvky[0])/70)
            if nr > 1: ws_obj.row_dimensions[riadok].height = 15 * nr
            ws_obj[f"B{riadok}"].value = prvky[0]
            ws_obj.cell(row=riadok, column=2+6).value = prvky[1]
            if objednavka.dodavatel and objednavka.dodavatel.s_danou==AnoNie.ANO:
                ws_obj[f'G{prvy_riadok+pocet_riadkov}'].value = objednavka.predpokladana_cena * Decimal(dph)
            else:
                ws_obj[f'F{prvy_riadok+pocet_riadkov}'].value = objednavka.predpokladana_cena
            add_sum = False
        elif len(prvky) == 5:
            nr =  int(1+len(prvky[0])/35)
            if nr > 1: ws_obj.row_dimensions[riadok].height = 15 * nr
            ws_obj.cell(row=riadok, column=2+0).value = prvky[0]
            ws_obj.cell(row=riadok, column=2+1).value = prvky[1]
            val2 = float(prvky[2].strip().replace(",","."))
            ws_obj.cell(row=riadok, column=2+2).value = val2
            ws_obj.cell(row=riadok, column=2+2).number_format= "0.00"
            val3 = float(prvky[3].strip().replace(",","."))
            ws_obj.cell(row=riadok, column=2+3).value = val3
            ws_obj.cell(row=riadok, column=2+4).number_format= "0.00"
            ws_obj.cell(row=riadok, column=2+6).value = prvky[4]
            #
            if objednavka.dodavatel and objednavka.dodavatel.s_danou==AnoNie.ANO:
                #nefunguje, ktovie prečo
                #ws_obj[f'G{riadok}'] = f'=IF(ISBLANK(D{riadok});" ";D{riadok}*E{riadok})'
                ws_obj[f'G{riadok}'] = val2*val3*dph
            else:
                ws_obj[f'F{riadok}'] = val2*val3
            add_sum = True

        if add_sum: 
            if objednavka.dodavatel and objednavka.dodavatel.s_danou==AnoNie.ANO:
                ws_obj[f'G{prvy_riadok+pocet_riadkov}'] = f"=SUM(G{prvy_riadok}:G{prvy_riadok+pocet_riadkov-1})"
            else:
                ws_obj[f'F{prvy_riadok+pocet_riadkov}'] = f"=SUM(F{prvy_riadok}:F{prvy_riadok+pocet_riadkov-1})"
    return ws_obj, prvy_riadok, pocet_riadkov

# lokálna funkcia, nemá zmysel ju volať zvonka
def OtvoritSablonuObjednavky():
    #úvodné testy
    objednavky_dir_path  = os.path.join(settings.MEDIA_ROOT,settings.OBJEDNAVKY_DIR)
    if not os.path.isdir(objednavky_dir_path):
        os.makedirs(objednavky_dir_path)
    
    #Načítať súbor šablóny
    nazov_objektu = "Šablóna objednávky"  #Presne takto musí byť objekt pomenovaný
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
    workbook = OtvoritSablonuObjednavky()
    if type(workbook) != Workbook:
        return workbook #Error

    ws_obj, prvy_riadok, pocet_riadkov = VyplnitHarok(workbook["Žiadanka"], objednavka, False)

    ws_obj[f"A{prvy_riadok+pocet_riadkov+3}"].value = objednavka.predmet
    if objednavka.termin_dodania:
        ws_obj[f"A{prvy_riadok+pocet_riadkov+4}"].value = ws_obj[f"A{prvy_riadok+pocet_riadkov+4}"].value.replace("[[termin_dodania]]", objednavka.termin_dodania)
    else:
        ws_obj[f"A{prvy_riadok+pocet_riadkov+4}"].value = ws_obj[f"A{prvy_riadok+pocet_riadkov+4}"].value.replace("[[termin_dodania]]", "")
    if not objednavka.datum_vytvorenia:
        return messages.ERROR, "Vytváranie súboru objednávky zlyhalo, lebo objednávka nemá zadaný dátum vytvorenia.", None
    ws_obj[f"A{prvy_riadok+pocet_riadkov+6}"].value = ws_obj[f"A{prvy_riadok+pocet_riadkov+6}"].value.replace("[[datum]]", objednavka.datum_vytvorenia.strftime("%d. %m. %Y"))
  
    ws_kl = workbook["Finančná kontrola žiadanka"]
    ws_kl["A1"].value = ws_kl["A1"].value.replace("[[cislo]]", objednavka.cislo[2:])
    vytvorene = objednavka.history.first().history_date
    #ws_kl["A1"].value = ws_kl["A1"].value.replace("[[datum]]", vytvorene.strftime("%d. %m. %Y"))
    ws_kl["A1"].value = ws_kl["A1"].value.replace("[[datum]]", objednavka.datum_vytvorenia.strftime("%d. %m. %Y"))

    #uložiť
    workbook.remove_sheet(workbook.get_sheet_by_name("Objednávka"))
    workbook.remove_sheet(workbook.get_sheet_by_name("Finančná kontrola objednávka"))
    #Create directory admin.rs_login if necessary
    nazov = f'{objednavka.cislo[2:]}-ziadanka.xlsx'
    opath = os.path.join(settings.OBJEDNAVKY_DIR,nazov)
    workbook.save(os.path.join(settings.MEDIA_ROOT,opath))
    return messages.SUCCESS, f"Súbor žiadanky {objednavka.cislo[2:]} bol úspešne vytvorený ({opath}).", opath
