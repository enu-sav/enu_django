# rozne utilitky

import os, locale
from ipdb import set_trace as trace
from django.utils.safestring import mark_safe
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from django.utils.html import format_html
from .models import SystemovySubor, PrijataFaktura, AnoNie, Objednavka, PrijataFaktura, Rozhodnutie, Zmluva
from .models import DoVP, DoPC, DoBPS, Poistovna, TypDochodku, Mena, PravidelnaPlatba, TypPP, TypPokladna, Pokladna
from .models import NajomneFaktura, PrispevokNaRekreaciu, Zamestnanec, OdmenaOprava, OdmenaAleboOprava, TypNepritomnosti, Nepritomnost
from .models import PlatovaStupnica 

from openpyxl import load_workbook
from openpyxl.styles import Font, Color, colors, Alignment, PatternFill , numbers
from openpyxl.utils import get_column_letter

import datetime, calendar, re

def leapdays(datefrom, dateto):
    yearfrom = datefrom.year
    if datefrom >= datetime.date(yearfrom, 3, 1): yearfrom += 1
    yearto = dateto.year
    if dateto >= datetime.date(yearto, 3, 1): yearto += 1
    return calendar.leapdays(yearfrom, yearto)

def locale_format(d):
    return locale.format('%%0.%df' % (-d.as_tuple().exponent), d, grouping=True)

# konvertuje Decimal sumu v tvare XYZ.ab do textoveho retazca
def decimal2text(num):
    s = {
        '0': '',
        '1': 'sto',
        '2': 'dvesto',
        '3': 'tristo',
        '4': 'štyristo',
        '5': 'päťsto',
        '6': 'šesťsto',
        '7': 'sedemsto',
        '8': 'osemsto',
        '9': 'deväťsto',
    }
    d = {
        '0': '',
        '2': 'dvadsať',
        '3': 'tridsať',
        '4': 'štyridsať',
        '5': 'päťdesiat',
        '6': 'šesťdesiat',
        '7': 'sedemdesiat',
        '8': 'osemdesiat',
        '9': 'deväťdesiat',
    }
    j = {
        '0': '',
        '1': 'jeden',
        '2': 'dva',
        '3': 'tri',
        '4': 'štyri',
        '5': 'päť',
        '6': 'šesť',
        '7': 'sedem',
        '8': 'osem',
        '9': 'deväť'
    }
    dj = {
        '10': 'desať',
        '11': 'jedenásť',
        '12': 'dvanásť',
        '13': 'trinásť',
        '14': 'štrnásť',
        '15': 'pätnásť',
        '16': 'šestnásť',
        '17': 'sedemnásť',
        '18': 'osemnásť',
        '19': 'devätnásť'
    }
    num=num.copy_abs()
    inum=int(num)
    nnum = "%03d"%num
    frac = " EUR %d/100"%(int(100*(num-inum)))
    if nnum[1] == "1":
        return s[nnum[0]] + dj[nnum[1:3]] + frac
    else:
        return s[nnum[0]] + d[nnum[1]] + j[nnum[2]] + frac

def meno_priezvisko(autor):
    if autor.titul_pred_menom:
        mp = f"{autor.titul_pred_menom} {autor.meno} {autor.priezvisko}"
    else:
        mp = f"{autor.meno} {autor.priezvisko}"
    if autor.titul_za_menom:
        mp = f"{mp}, {autor.titul_za_menom}"
    return mp.strip()

def adresa(osoba):
    if osoba.adresa_ulica:
        return f"{osoba.adresa_ulica}, {osoba.adresa_mesto}, {osoba.adresa_stat}".strip()
    else:
        return f"{osoba.adresa_mesto}, {osoba.adresa_stat}".strip()
 
# pouzivatel: aktualny pouzivatel
# PrispevokNaRekreaciu
def VytvoritKryciListRekreacia(platba, pouzivatel):
    #úvodné testy
    if not os.path.isdir(settings.PLATOBNE_PRIKAZY_DIR):
        os.makedirs(settings.PLATOBNE_PRIKAZY_DIR)
    
    #Načítať súbor šablóny
    nazov_objektu = "Šablóna krycieho listu: vyúčtovanie žiadosti o príspevok na rekreáciu"  #Presne takto musí byť objekt pomenovaný
    sablona = SystemovySubor.objects.filter(subor_nazov = nazov_objektu)
    if not sablona:
        return messages.ERROR, f"V systéme nie je definovaný súbor '{nazov_objektu}'.", None
    nazov_suboru = sablona[0].subor.file.name 
    workbook = load_workbook(filename=nazov_suboru)
    ws = workbook.active
    ws[f'C2'].value = platba.cislo
    ws[f'F2'].value = meno_priezvisko(platba.zamestnanec)
    ws[f'B3'].value = datetime.date.today().strftime('%d. %m. %Y')
    ws[f'D21'].value = f"{platba.zdroj.kod} ({platba.zdroj.popis})"
    ws[f'D22'].value = f"{platba.zakazka.kod} ({platba.zakazka.popis})"
    ws[f'D23'].value = f"{platba.ekoklas.kod} ({platba.ekoklas.nazov})"
    ws[f'D24'].value = f"{platba.cinnost.kod} ({platba.cinnost.nazov})"

    #ulozit
    nazov = platba.zamestnanec.priezvisko
    nazov = f"{platba.zamestnanec.priezvisko}-{platba.cislo}.xlsx"
    opath = os.path.join(settings.REKREACIA_DIR,nazov)
    workbook.save(os.path.join(settings.MEDIA_ROOT,opath))
    return messages.SUCCESS, mark_safe(f"Súbor krycieho listu vyúčtovania príspevku na rekreáciu {platba.cislo} bol úspešne vytvorený ({opath}). <br />Krycí list a vyúčtovanie dajte na podpis. <br />Po podpísaní dajte krycí list a vyúčtovanie na sekretariát na odoslanie a vyplňte pole 'Dátum odoslania KL'."), opath
 

# pouzivatel: aktualny pouzivatel
def VytvoritKryciListOdmena(platba, pouzivatel):
    #úvodné testy
    if not os.path.isdir(settings.PLATOBNE_PRIKAZY_DIR):
        os.makedirs(settings.PLATOBNE_PRIKAZY_DIR)
    
    lt="[["
    gt="]]"

    #Načítať súbor šablóny
    nazov_objektu = "Šablóna pre odmenu"  #Presne takto musí byť objekt pomenovaný
    sablona = SystemovySubor.objects.filter(subor_nazov = nazov_objektu)
    if not sablona:
        return messages.ERROR, f"V systéme nie je definovaný súbor '{nazov_objektu}'.", None
    nazov_suboru = sablona[0].subor.file.name 
 
    try:
        with open(nazov_suboru, "r") as f:
            text = f.read()
    except:
        return messages.ERROR, f"Chyba pri vytváraní súboru krycieho listu: chyba pri čítaní šablóny '{nazov_suboru}'", None
    
    # vložiť údaje
    #
    locale.setlocale(locale.LC_ALL, 'sk_SK.UTF-8')
    text = text.replace(f"{lt}datum{gt}", timezone.now().strftime("%d. %m. %Y"))
    text = text.replace(f"{lt}zdroj{gt}", f"{platba.zdroj.kod} ({platba.zdroj.popis})")
    text = text.replace(f"{lt}zakazka{gt}", f"{platba.zakazka.kod} ({platba.zakazka.popis})")
    text = text.replace(f"{lt}ekoklas{gt}", f"{platba.ekoklas.kod} ({platba.ekoklas.nazov})")
    text = text.replace(f"{lt}cinnost{gt}", f"{platba.cinnost.kod} ({platba.cinnost.nazov})")
    text = text.replace(f"{lt}doklad{gt}", platba.cislo)
    if platba.typ == OdmenaAleboOprava.ODMENAS:
        text = text.replace(f"{lt}coho{gt}", "odmien")
        text = text.replace('text:name="Zdovodnenie"', f'text:name="Zdovodnenie" text:display="none"')
        nazov = f"Odmeny-{platba.cislo}.fodt"
    else:
        if platba.typ == OdmenaAleboOprava.ODMENA:
            typ = "odmeny"
        if platba.typ == OdmenaAleboOprava.ODCHODNE:
            typ = "odchodného"
        if platba.typ == OdmenaAleboOprava.ODSTUPNE:
            typ = "odstupného"
        text = text.replace(f"{lt}coho{gt}", typ)
        text = text.replace(f"{lt}menotitul{gt}", platba.zamestnanec.menopriezvisko(titul=True))
        text = text.replace(f"{lt}osobnecislo{gt}", platba.zamestnanec.cislo_zamestnanca)
        text = text.replace(f"{lt}odmena1{gt}", str(-platba.suma))
        text = text.replace(f"{lt}dovod{gt}", platba.zdovodnenie)
        nazov = f"{platba.zamestnanec.priezviskomeno()}-{platba.cislo}.fodt".replace(' ','-').replace("/","-")
    #ulozit
    opath = os.path.join(settings.ODMENY_DIR,nazov)
    with open(os.path.join(settings.MEDIA_ROOT,opath), "w") as f:
        f.write(text)
    return messages.SUCCESS, mark_safe(f"Súbor priznania odmeny/odchodného/odstupného a krycieho listu {platba.cislo} bol úspešne vytvorený ({opath}). <br />Krycí list a priznanie dajte na podpis. Po odoslaní krycieho listu a priznania vyplňte pole 'Dátum odoslania KL'."), opath

# pouzivatel: aktualny pouzivatel
def VytvoritKryciList(platba, pouzivatel):
    #úvodné testy
    if not os.path.isdir(settings.PLATOBNE_PRIKAZY_DIR):
        os.makedirs(settings.PLATOBNE_PRIKAZY_DIR)
    
    lt="[["
    gt="]]"

    #Načítať súbor šablóny
    nazov_objektu = "Šablóna krycieho listu bez platby"  #Presne takto musí byť objekt pomenovaný
    sablona = SystemovySubor.objects.filter(subor_nazov = nazov_objektu)
    if not sablona:
        return messages.ERROR, f"V systéme nie je definovaný súbor '{nazov_objektu}'.", None
    nazov_suboru = sablona[0].subor.file.name 
 
    try:
        with open(nazov_suboru, "r") as f:
            text = f.read()
    except:
        return messages.ERROR, f"Chyba pri vytváraní súboru krycieho listu: chyba pri čítaní šablóny '{nazov_suboru}'", None
    
    # vložiť údaje
    #
    if type(platba) == NajomneFaktura:
        text = text.replace(f"{lt}popis{gt}", f"Platba č. {platba.cislo_softip}")
        nazov = platba.zmluva.najomnik.nazov
        meno_pola = "Dané na vybavenie dňa"
    else:
        text = text.replace(f"{lt}popis{gt}", "")
    text = text.replace(f"{lt}zdroj{gt}", f"{platba.zdroj.kod} ({platba.zdroj.popis})")
    text = text.replace(f"{lt}zakazka{gt}", f"{platba.zakazka.kod} ({platba.zakazka.popis})")
    text = text.replace(f"{lt}ekoklas{gt}", f"{platba.ekoklas.kod} ({platba.ekoklas.nazov})")
    text = text.replace(f"{lt}cinnost{gt}", f"{platba.cinnost.kod} ({platba.cinnost.nazov})")
    locale.setlocale(locale.LC_ALL, 'sk_SK.UTF-8')
    text = text.replace(f"{lt}akt_datum{gt}", timezone.now().strftime("%d. %m. %Y"))
    #ulozit
    if "," in nazov: nazov = nazov[:nazov.find(",")]
    nazov = f"{nazov}-{platba.cislo}.fodt".replace(' ','-').replace("/","-")
    opath = os.path.join(settings.PLATOBNE_PRIKAZY_DIR,nazov)
    with open(os.path.join(settings.MEDIA_ROOT,opath), "w") as f:
        f.write(text)
    return messages.SUCCESS, mark_safe(f"Súbor krycieho listu platby {platba.cislo} bol úspešne vytvorený ({opath}). <br />Krycí list a vyúčtovanie dajte na podpis. <br />Po podpísaní krycí list a vyúčtovanie dajte na sekretariát na odoslanie a vyplňte pole '{meno_pola}'."), opath
 
# pouzivatel: aktualny pouzivatel
def VytvoritPlatobnyPrikazIP(faktura, pouzivatel):
    #úvodné testy
    if not os.path.isdir(settings.PLATOBNE_PRIKAZY_DIR):
        os.makedirs(settings.PLATOBNE_PRIKAZY_DIR)
    
    lt="[["
    gt="]]"

    #Načítať súbor šablóny
    nazov_objektu = "Šablóna interný prevod"  #Presne takto musí byť objekt pomenovaný
    sablona = SystemovySubor.objects.filter(subor_nazov = nazov_objektu)
    if not sablona:
        return messages.ERROR, f"V systéme nie je definovaný súbor '{nazov_objektu}'.", None
    nazov_suboru = sablona[0].subor.file.name 
 
    try:
        with open(nazov_suboru, "r") as f:
            text = f.read()
    except:
        return messages.ERROR, f"Chyba pri vytváraní súboru platobného príkazu interného prevodu: chyba pri čítaní šablóny '{nazov_suboru}'", None
    
    # vložiť údaje
    #
    text = text.replace(f"{lt}prevod_cislo{gt}", faktura.cislo)
    locale.setlocale(locale.LC_ALL, 'sk_SK.UTF-8')
    if faktura.suma:
        text = text.replace(f"{lt}DM{gt}", f"{locale_format(abs(faktura.suma))} €")     # vo formulári chceme kladné
        if faktura.suma > 0:
            text = text.replace(f"{lt}doda_odbe{gt}", "Odberateľ")
        else:
            text = text.replace(f"{lt}doda_odbe{gt}", "Dodávateľ")
    else:
        return messages.ERROR, "Vytváranie príkazu zlyhalo, lebo nebola zadaná suma.", None
    text = text.replace(f"{lt}prijimatel{gt}", faktura.partner.nazov)
    # ulica ne nepovinná (malá obec)
    if faktura.partner.adresa_ulica:
        text = text.replace(f"{lt}adresa1{gt}", faktura.partner.adresa_ulica)
    else:
        text = text.replace(f"{lt}adresa1{gt}", "")
    if not faktura.partner.adresa_mesto:
        return messages.ERROR, "Vytváranie príkazu zlyhalo, lebo adresa dodávateľa je nekompletná (mesto).", None
    else:
        text = text.replace(f"{lt}adresa2{gt}", faktura.partner.adresa_mesto)
    if not faktura.partner.adresa_stat:
        return messages.ERROR, "Vytváranie príkazu zlyhalo, lebo adresa dodávateľa je nekompletná (štát).", None
    else:
        text = text.replace(f"{lt}adresa3{gt}", faktura.partner.adresa_stat)
    text = text.replace(f"{lt}doslo_dna{gt}", faktura.doslo_datum.strftime("%d. %m. %Y"))
    text = text.replace(f"{lt}datum_splatnosti{gt}", 
            faktura.splatnost_datum.strftime("%d. %m. %Y") if faktura.splatnost_datum else "")
    #text = text.replace(f"{lt}predmet_faktury{gt}", faktura.predmet if jePF else TypPP(faktura.typ).label)
    text = text.replace(f"{lt}pouzivatel{gt}", pouzivatel.get_full_name())

    text = text.replace(f"{lt}ekoklas{gt}", faktura.ekoklas.kod)
    text = text.replace(f"{lt}zdroj{gt}", faktura.zdroj.kod)
    if faktura.zdroj.kod == '111' or faktura.zdroj.kod == '131L':
        text = text.replace(f"{lt}dph_neuctovat{gt}", "DPH neúčtovať")
    else:
        text = text.replace(f"{lt}dph_neuctovat{gt}", "")
    if faktura.partner.bankovy_kontakt:
        text = text.replace(f"{lt}IBAN{gt}", faktura.partner.bankovy_kontakt)
    else:
        text = text.replace(f"{lt}IBAN{gt}", "")
    text = text.replace(f"{lt}predmet{gt}", faktura.predmet)
    text = text.replace(f"{lt}na_zaklade{gt}", faktura.na_zaklade)
    text = text.replace(f"{lt}program{gt}", faktura.program.kod)
    text = text.replace(f"{lt}cinnost{gt}", faktura.cinnost.kod)
    text = text.replace(f"{lt}zakazka{gt}", faktura.zakazka.kod)
    text = text.replace(f"{lt}akt_datum{gt}", timezone.now().strftime("%d. %m. %Y"))
    #ulozit
    #Create directory admin.rs_login if necessary
    nazov = faktura.partner.nazov
    if "," in nazov: nazov = nazov[:nazov.find(",")]
    nazov = f"{nazov}-{faktura.cislo}.fodt".replace(' ','-').replace("/","-")
    opath = os.path.join(settings.PLATOBNE_PRIKAZY_DIR,nazov)
    with open(os.path.join(settings.MEDIA_ROOT,opath), "w") as f:
        f.write(text)
    return messages.SUCCESS, mark_safe(f"Súbor platobného príkazu internej platby {faktura.cislo} bol úspešne vytvorený ({opath}). Príkaz dajte na podpis. <br />Ak treba, údaje platby možno ešte upravovať. Po každej úprave treba vytvoriť nový platobný príkaz opakovaním akcie.<br />Po podpísaní príkaz dajte na sekretariát na odoslanie a vyplňte pole 'Dané na úhradu dňa'."), opath
 
# pouzivatel: aktualny pouzivatel
def VytvoritPlatobnyPrikaz(faktura, pouzivatel):
    #úvodné testy
    if not os.path.isdir(settings.PLATOBNE_PRIKAZY_DIR):
        os.makedirs(settings.PLATOBNE_PRIKAZY_DIR)
    
    lt="[["
    gt="]]"

    jePF = type(faktura) == PrijataFaktura

    #Načítať súbor šablóny
    nazov_objektu = "Šablóna platobný príkaz"  #Presne takto musí byť objekt pomenovaný
    sablona = SystemovySubor.objects.filter(subor_nazov = nazov_objektu)
    if not sablona:
        return messages.ERROR, f"V systéme nie je definovaný súbor '{nazov_objektu}'.", None
    nazov_suboru = sablona[0].subor.file.name 
 
    try:
        with open(nazov_suboru, "r") as f:
            text = f.read()
    except:
        return messages.ERROR, f"Chyba pri vytváraní súboru platobného príkazu faktúry: chyba pri čítaní šablóny '{nazov_suboru}'", None
    
    # vložiť údaje
    #
    text = text.replace(f"{lt}nasa_faktura_cislo{gt}", faktura.cislo)
    locale.setlocale(locale.LC_ALL, 'sk_SK.UTF-8')
    if not faktura.suma and not faktura.sumacm:
        return messages.ERROR, "Vytváranie príkazu zlyhalo, lebo nebola zadaná suma v Eur a ani suma v cudzej mene.", None
    if jePF:    #faktúra môže byť aj v cudzej mene
        if faktura.mena == Mena.EUR:
            text = text.replace(f"{lt}DM{gt}", f"{locale_format(-faktura.suma)} €")     # suma je záporná, vo formulári chceme kladné
            text = text.replace(f"{lt}CM{gt}", "")
        else:
            text = text.replace(f"{lt}CM{gt}", f"{locale_format(-faktura.sumacm)} {faktura.mena}")    # suma je záporná, vo formulári chceme kladné
            text = text.replace(f"{lt}DM{gt}", "")
    else:   #len v EUR
        text = text.replace(f"{lt}DM{gt}", f"{locale_format(-faktura.suma)} €")     # suma je záporná, o formulári chceme kladné
        text = text.replace(f"{lt}CM{gt}", "")
    text = text.replace(f"{lt}dodavatel{gt}", faktura.objednavka_zmluva.dodavatel.nazov)
    # ulica ne nepovinná (malá obec)
    if faktura.objednavka_zmluva.dodavatel.adresa_ulica:
        text = text.replace(f"{lt}adresa1{gt}", faktura.objednavka_zmluva.dodavatel.adresa_ulica)
    else:
        text = text.replace(f"{lt}adresa1{gt}", "")
    if not faktura.objednavka_zmluva.dodavatel.adresa_mesto:
        return messages.ERROR, "Vytváranie príkazu zlyhalo, lebo adresa dodávateľa je nekompletná (mesto).", None
    else:
        text = text.replace(f"{lt}adresa2{gt}", faktura.objednavka_zmluva.dodavatel.adresa_mesto)
    if not faktura.objednavka_zmluva.dodavatel.adresa_stat:
        return messages.ERROR, "Vytváranie príkazu zlyhalo, lebo adresa dodávateľa je nekompletná (štát).", None
    else:
        text = text.replace(f"{lt}adresa3{gt}", faktura.objednavka_zmluva.dodavatel.adresa_stat)
    text = text.replace(f"{lt}dodavatel_faktura{gt}", 
            faktura.dcislo if jePF and faktura.dcislo else "")
    text = text.replace(f"{lt}doslo_dna{gt}", 
            faktura.doslo_datum.strftime("%d. %m. %Y") if jePF and faktura.doslo_datum else "" )
    text = text.replace(f"{lt}datum_splatnosti{gt}", 
            faktura.splatnost_datum.strftime("%d. %m. %Y") if faktura.splatnost_datum else "")
    text = text.replace(f"{lt}predmet_faktury{gt}", faktura.predmet if jePF else TypPP(faktura.typ).label)
    text = text.replace(f"{lt}pouzivatel{gt}", pouzivatel.get_full_name())

    if type(faktura.objednavka_zmluva) == Objednavka:
        text = text.replace(f"{lt}obj_zmluva{gt}", "objednávka")
        text = text.replace(f"{lt}oz_cislo{gt}", faktura.objednavka_zmluva.objednavka.cislo)
        if not faktura.objednavka_zmluva.objednavka.datum_vytvorenia:
            return messages.ERROR, "Vytváranie príkazu zlyhalo, lebo objednávka nemá zadaný dátum vytvorenia.", None
        text = text.replace(f"{lt}zo_dna{gt}", faktura.objednavka_zmluva.objednavka.datum_vytvorenia.strftime("%d. %m. %Y"))
        pass
    elif type(faktura.objednavka_zmluva) == Zmluva:
        text = text.replace(f"{lt}obj_zmluva{gt}", "zmluva")
        text = text.replace(f"{lt}oz_cislo{gt}", faktura.objednavka_zmluva.zmluva.cislo)
        if not faktura.objednavka_zmluva.zmluva.datum_zverejnenia_CRZ:
            return messages.ERROR, "Vytváranie príkazu zlyhalo, lebo zmluva nemá zadaný dátum platnosti.", None
        text = text.replace(f"{lt}zo_dna{gt}", faktura.objednavka_zmluva.zmluva.datum_zverejnenia_CRZ.strftime("%d. %m. %Y"))
        pass
    else:   #Rozhodnutie
        text = text.replace(f"{lt}obj_zmluva{gt}", "rozhodnutie")
        text = text.replace(f"{lt}oz_cislo{gt}", faktura.objednavka_zmluva.rozhodnutie.cislo)
        text = text.replace(f"{lt}zo_dna{gt}", faktura.objednavka_zmluva.rozhodnutie.datum_vydania.strftime("%d. %m. %Y"))
        pass

    text = text.replace(f"{lt}ekoklas{gt}", faktura.ekoklas.kod)
    text = text.replace(f"{lt}zdroj{gt}", faktura.zdroj.kod)
    if faktura.zdroj.kod == '111' or faktura.zdroj.kod == '131L':
        text = text.replace(f"{lt}dph_neuctovat{gt}", "DPH neúčtovať")
    else:
        text = text.replace(f"{lt}dph_neuctovat{gt}", "")
    text = text.replace(f"{lt}program{gt}", faktura.program.kod)
    text = text.replace(f"{lt}cinnost{gt}", faktura.cinnost.kod)
    text = text.replace(f"{lt}zakazka{gt}", faktura.zakazka.kod)
    text = text.replace(f"{lt}akt_datum{gt}", timezone.now().strftime("%d. %m. %Y"))
    #ulozit
    #Create directory admin.rs_login if necessary
    nazov = faktura.objednavka_zmluva.dodavatel.nazov
    if "," in nazov: nazov = nazov[:nazov.find(",")]
    nazov = f"{nazov}-{faktura.cislo}.fodt".replace(' ','-').replace("/","-")
    opath = os.path.join(settings.PLATOBNE_PRIKAZY_DIR,nazov)
    with open(os.path.join(settings.MEDIA_ROOT,opath), "w") as f:
        f.write(text)
    return messages.SUCCESS, mark_safe(f"Súbor platobného príkazu faktúry {faktura.cislo} bol úspešne vytvorený ({opath}). Príkaz dajte na podpis. <br />Ak treba, údaje platby možno ešte upravovať. Po každej úprave treba vytvoriť nový platobný príkaz opakovaním akcie.<br />Po podpísaní príkaz dajte na sekretariát na odoslanie a vyplňte pole 'Dané na úhradu dňa'."), opath


# skryt sekciu v dokumente dohody
#sekcia: napr. 'text:name="DoBPS_podmienky"'. Zoznam je vo funkcii dohoda_skryt_sekcie
def dohoda_skryt_sekciu(text, sekcia):
    return text.replace(sekcia, f'{sekcia} text:display="none"')

# dtype: sekcia podľa typu zmluvy, ktorá sa má zachovať 
def dohoda_skryt_sekcie(text, dtype):
    #Sekcie v dokumente, ktoré možno skryť 
    #Po pridaní novej sekcie treba sem pridať
    sekcie = [
        'text:name="DoBPS_podmienky"',
        'text:name="DoVP_vyplata"',
        'text:name="DoPC_vyplata"',
        'text:name="DoBPS_vyplata"',
        'text:name="DoPC_DoBPS_paska"',
        'text:name="DoPC_DoVP_vyhlasenie"',
        'text:name="DoBPS_vyhlasenie"',
        'text:name="DoBPS_priloha"',
        'text:name="DoVP_pomocnik"'
    ]
    for sekcia in sekcie:
       if not dtype in sekcia:
        text = text.replace(sekcia, f'{sekcia} text:display="none"')
    return text

def OveritUdajeDohodara(dohodar):
    chyby = ""
    if not dohodar.meno: chyby = f"{chyby} meno,"
    if not dohodar.priezvisko: chyby = f"{chyby} priezvisko,"
    if not dohodar.rodne_cislo: chyby = f"{chyby} rodné číslo,"
    if not dohodar.bankovy_kontakt: chyby = f"{chyby} bankový kontakt,"
    if not dohodar.adresa_mesto: chyby = f"{chyby} PSČ a mesto,"
    # ulica sa netestuje, môže byť nezadaná
    #if not dohodar.adresa_ulica: chyby = f"{chyby} ulica,"
    if not dohodar.adresa_stat: chyby = f"{chyby} štát,"
    if not dohodar.miesto_nar: chyby = f"{chyby} miesto narodenia," 
    if not dohodar.cop: chyby = f"{chyby} číslo obč. preukazu,"
    if not dohodar.datum_nar: chyby = f"{chyby} dátum narodenia," 
    if not dohodar.poistovna: chyby = f"{chyby} zdravotná poisťovňa," 
    if not dohodar.email: chyby = f"{chyby} email,"
    if not dohodar.stav: chyby = f"{chyby} rodinný stav,"
    if not dohodar.st_prislusnost: chyby = f"{chyby} štátna príslušnosť,"
    if not dohodar.poberatel_doch: chyby = f"{chyby} poberateľ dôchodku," 
    if dohodar.poberatel_doch == AnoNie.ANO:
        if not dohodar.typ_doch: chyby = f"{chyby} typ dôchodku," 
        if not dohodar.datum_doch: chyby = f"{chyby} dátum vzniku dôchodku," 
    if dohodar.ztp == AnoNie.ANO:
        if not dohodar.datum_ztp: chyby = f"{chyby} dátum vzniku ZŤP," 
    return chyby.strip(" ").strip(",")


# Vytvorí dohodu, krycí list a všetko, čo k tomu treba
def VytvoritSuborDohody(dohoda):
    chyby = OveritUdajeDohodara(dohoda.zmluvna_strana)
    if chyby:
        return messages.ERROR, f"Dohoda nebola vytvorená, lebo údaje dohodára sú nekomplentné. Chýba: {chyby}", None

    #úvodné testy
    dohody_dir_path  = os.path.join(settings.MEDIA_ROOT,settings.DOHODY_DIR)
    if not os.path.isdir(dohody_dir_path):
        os.makedirs(dohody_dir_path)
    
    #Načítať súbor šablóny
    nazov_objektu = "Šablóna dohody"  #Presne takto musí byť objekt pomenovaný
    sablona = SystemovySubor.objects.filter(subor_nazov = nazov_objektu)
    if not sablona:
        return messages.ERROR, f"V systéme nie je definovaný súbor '{nazov_objektu}'.", None
    nazov_suboru = sablona[0].subor.file.name 
 
    try:
        with open(nazov_suboru, "r") as f:
            text = f.read()
    except:
        return messages.ERROR, f"Chyba pri vytváraní súboru platobného príkazu faktúry: chyba pri čítaní šablóny '{nazov_suboru}'", None
    
    #Create directory admin.rs_login if necessary
    # vložiť spoločné údaje
    dohodar = dohoda.zmluvna_strana
    text = text.replace("[[meno_priezvisko]]", meno_priezvisko(dohodar))
    if dohodar.rod_priezvisko:
        text = text.replace("[[rod_priezvisko]]", f", rod. priezvisko: {dohodar.rod_priezvisko}")
    else:
        text = text.replace("[[rod_priezvisko]]", "")
    text = text.replace("[[adresa]]", adresa(dohodar))
    text = text.replace("[[d_narodenia]]", dohodar.datum_nar.strftime("%d. %m. %Y"))
    text = text.replace("[[m_narodenia]]", dohodar.miesto_nar)
    text = text.replace("[[cop]]", dohodar.cop)
    text = text.replace("[[rc]]", dohodar.rodne_cislo)
    text = text.replace("[[stav]]", dohodar.stav)
    text = text.replace("[[st_prislusnost]]", dohodar.st_prislusnost)
    text = text.replace("[[zdrav_poistovna]]", Poistovna(dohodar.poistovna).label)
    text = text.replace("[[IBAN]]", dohodar.bankovy_kontakt)
    text = text.replace("[[email]]", dohodar.email)
    if dohodar.poberatel_doch == AnoNie.ANO:
        text = text.replace( "[[dochodok]]", 
                f"{AnoNie(dohodar.poberatel_doch).label}, {TypDochodku(dohodar.typ_doch).label}, dátum vzniku: {dohodar.datum_doch.strftime('%d. %m. %Y')}")
    else:
        text = text.replace("[[dochodok]]", AnoNie(dohodar.poberatel_doch).label)
    if dohodar.ztp == AnoNie.ANO:
        text = text.replace( "[[ztp]]", 
                f"{AnoNie(dohodar.ztp).label}, od {dohodar.datum_ztp.strftime('%d. %m. %Y')}")
    else:
        if dohodar.ztp:
            text = text.replace("[[ztp]]", AnoNie(dohodar.ztp).label)
        else:
            text = text.replace("[[ztp]]", AnoNie("nie").label)

    text = text.replace("[[dohodnuta_cinnost]]", dohoda.predmet)
    text = text.replace("[[cislo]]", dohoda.cislo)
    text = text.replace("[[datum_od]]", dohoda.datum_od.strftime("%d. %m. %Y"))
    text = text.replace("[[datum_do]]", dohoda.datum_do.strftime("%d. %m. %Y"))
    text = text.replace("[[datum]]", timezone.now().strftime("%d. %m. %Y"))
    text = text.replace("[[zdroj]]", dohoda.zdroj.kod)
    text = text.replace("[[zakazka]]", dohoda.zakazka.kod)

    # vložiť údaje DoVP
    if type(dohoda) == DoVP:
        text = text.replace("[[typ_dohody]]", "o vykonaní práce")
        text = text.replace("[[zakony]]", "§ 223 – § 225 a § 226")
        text = text.replace("[[odmena]]", f"{dohoda.odmena_celkom} Eur")
        text = text.replace("[[rozsah_prace_cas]]", f"{dohoda.hod_celkom} hodín")
        if dohoda.pomocnik:
            text = text.replace("[[osobne_pomoc]]", "za pomoci rod. príslušníkov ")
            text = text.replace("[[pomocnik]]", dohoda.pomocnik)
        else:
            text = text.replace("[[osobne_pomoc]]", "osobne")
            text = text.replace("[[pomocnik]]", "")
        text = text.replace("[[vyplatny_termin]]", dohoda.datum_do.strftime("%m/%Y")) 
        text = dohoda_skryt_sekcie(text, "DoVP")
        if dohodar.poberatel_doch == AnoNie.NIE:
            text = dohoda_skryt_sekciu(text, 'text:name="DoPC_DoVP_vyhlasenie"')
    # vložiť údaje DoPC
    elif type(dohoda) == DoPC:
        if dohoda.dodatok_k:
            text = text.replace("[[typ_dohody]]", f"o pracovnej činnosti (dodatok č.{dohoda.cislo[-1]})")
        else:
            text = text.replace("[[typ_dohody]]", "o pracovnej činnosti")
        text = text.replace("[[zakony]]", "§ 223 – § 225 a § 228a")
        text = text.replace("[[odmena]]", f"{dohoda.odmena_mesacne} Eur mesačne")
        text = text.replace("[[rozsah_prace_cas]]", f"{dohoda.hod_mesacne} hodín mesačne")
        text = dohoda_skryt_sekcie(text, "DoPC")
        if dohodar.poberatel_doch == AnoNie.NIE:
            text = dohoda_skryt_sekciu(text, 'text:name="DoPC_DoVP_vyhlasenie"')
    # vložiť údaje DoBPS
    elif type(dohoda) == DoBPS:
        text = text.replace("[[typ_dohody]]", "o brigádnickej práci študentov")
        text = text.replace("[[zakony]]", "§ 223 – § 225, § 227 a § 228")
        text = text.replace("[[odmena]]", f"{dohoda.odmena_mesacne} Eur mesačne")
        text = text.replace("[[rozsah_prace_cas]]", "asdf")
        text = dohoda_skryt_sekcie(text, "DoBPS")
        #text.replace("[[preberajuca_osoba]]", "asdf")

    nazov = f"{dohoda.cislo}-{dohoda.zmluvna_strana.priezvisko}.fodt"
    opath = os.path.join(settings.DOHODY_DIR,nazov)
    with open(os.path.join(settings.MEDIA_ROOT,opath), "w") as f:
        f.write(text)
    return messages.SUCCESS, f"Súbor dohody {dohoda.cislo} bol úspešne vytvorený ({opath}).", opath

def VytvoritSuborObjednavky(objednavka):
    DPH = 1.2
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

    obj = workbook["Objednávka"]
    obj["A3"].value = obj["A3"].value.replace("[[cislo]]",objednavka.cislo)
    #dodávateľ
    obj["D6"].value = objednavka.dodavatel.nazov
    obj["D7"].value = objednavka.dodavatel.adresa_ulica
    obj["D8"].value = objednavka.dodavatel.adresa_mesto
    obj["D9"].value = objednavka.dodavatel.adresa_stat

    #položky
    prvy_riadok = 15 #prvy riadok tabulky
    pocet_riadkov = 15
    add_sum = True  # či s má do posledného riadka vložiť súčet
    for rr, polozka in enumerate(objednavka.objednane_polozky.split("\n")):
        riadok = prvy_riadok+rr
        prvky = polozka.split(";")
        if len(prvky) == 1:  #zlúčiť bunky
            obj.merge_cells(f'B{riadok}:F{riadok}')
            obj[f"B{riadok}"].value = prvky[0]
            add_sum = False
        elif len(prvky) == 4:
            obj.cell(row=riadok, column=2+0).value = prvky[0]
            obj.cell(row=riadok, column=2+1).value = prvky[1]
            val2 = float(prvky[2].strip().replace(",","."))
            obj.cell(row=riadok, column=2+2).value = val2
            obj.cell(row=riadok, column=2+2).number_format= "0.00"
            val3 = float(prvky[3].strip().replace(",","."))
            obj.cell(row=riadok, column=2+3).value = val3
            obj.cell(row=riadok, column=2+4).number_format= "0.00"
            #nefunguje, ktovie prečo
            #
            if objednavka.dodavatel.s_danou==AnoNie.ANO:
                #obj[f'G{riadok}'] = f'=IF(ISBLANK(D{riadok});" ";D{riadok}*E{riadok})'
                obj[f'G{riadok}'] = val2*val3*DPH
            else:
                obj[f'F{riadok}'] = val2*val3
            obj.cell(row=riadok, column=2+5).number_format= "0.00"
            add_sum = True
        else:
            return messages.ERROR, f"Riadok {rr+1} zoznamu položiek má nesprávny počet polí (počet poĺí {len(prvky)}, počet bodkočiarok {len(prvky) -1}). Text upravte tak, aby mal práve 4 polia (3 bodkočiarky) alebo všetky bodkočiarky odstráňte. Všetky riadky musia byť členené na polia rovnako.", None

        if add_sum: 
            if objednavka.dodavatel.s_danou==AnoNie.ANO:
                obj[f'G{prvy_riadok+pocet_riadkov}'] = f"=SUM(G{prvy_riadok}:G{prvy_riadok+pocet_riadkov-1})"
            else:
                obj[f'F{prvy_riadok+pocet_riadkov}'] = f"=SUM(F{prvy_riadok}:F{prvy_riadok+pocet_riadkov-1})"


    if objednavka.termin_dodania:
        obj["A32"].value = obj["A32"].value.replace("[[termin_dodania]]", objednavka.termin_dodania)
    else:
        obj["A32"].value = obj["A32"].value.replace("[[termin_dodania]]", "")
    if not objednavka.datum_vytvorenia:
        return messages.ERROR, "Vytváranie súboru objednávky zlyhalo, lebo objednávka nemá zadaný dátum vytvorenia.", None
    obj["A34"].value = obj["A34"].value.replace("[[datum]]", objednavka.datum_vytvorenia.strftime("%d. %m. %Y"))
  
    kl = workbook["Finančná kontrola"]
    kl["A1"].value = kl["A1"].value.replace("[[cislo]]", objednavka.cislo)
    kl["A1"].value = kl["A1"].value.replace("[[datum]]", objednavka.datum_vytvorenia.strftime("%d. %m. %Y"))

    #ulozit
    #Create directory admin.rs_login if necessary
    nazov = f'{objednavka.cislo}-{objednavka.dodavatel.nazov.replace(" ","").replace(".","").replace(",","-")}.xlsx'
    opath = os.path.join(settings.OBJEDNAVKY_DIR,nazov)
    workbook.save(os.path.join(settings.MEDIA_ROOT,opath))
    return messages.SUCCESS, f"Súbor objednávky {objednavka.cislo} bol úspešne vytvorený ({opath}).", opath

def VytvoritSuborVPD(vpd):
    #úvodné testy
    pokladna_dir_path  = os.path.join(settings.MEDIA_ROOT,settings.POKLADNA_DIR)
    if not os.path.isdir(pokladna_dir_path):
        os.makedirs(pokladna_dir_path)
    
    #Načítať súbor šablóny
    nazov_objektu = "Šablóna VPD"  #Presne takto musí byť objekt pomenovaný
    sablona = SystemovySubor.objects.filter(subor_nazov = nazov_objektu)
    if not sablona:
        return messages.ERROR, f"V systéme nie je definovaný súbor '{nazov_objektu}'.", None
    nazov_suboru = sablona[0].subor.file.name 
    workbook = load_workbook(filename=nazov_suboru)

    rok = re.findall(r"%s-([0-9]*).*"%Pokladna.oznacenie, vpd.cislo)[0]
    cislovpd = f"{vpd.cislo_VPD}/{rok}"
    obj = workbook["VPD"]
    obj["J2"].value = cislovpd
    obj["H5"].value = vpd.datum_transakcie.strftime("%d. %m. %Y")
    obj["D7"].value = meno_priezvisko(vpd.zamestnanec)
    obj["H10"].value = vpd.suma.copy_abs()
    #suma textom
    obj["D11"].value = decimal2text(vpd.suma)
    obj["C13"].value = vpd.popis
    obj["E21"].value = vpd.cislo

    kl = workbook["Krycí list"]
    kl["A2"].value = kl["A2"].value.replace("[[xx-xxxx]]", cislovpd) 
    kl["B10"].value = vpd.zdroj.kod
    kl["D10"].value = vpd.zakazka.kod
    kl["G10"].value = vpd.ekoklas.kod

    #ulozit
    #Create directory admin.rs_login if necessary

    nazov = f'VPD-{cislovpd}.xlsx'.replace("/","-")
    opath = os.path.join(settings.POKLADNA_DIR,nazov)
    workbook.save(os.path.join(settings.MEDIA_ROOT,opath))
    return messages.SUCCESS, f"Súbor {nazov} bol úspešne vytvorený.", opath

def UlozitStranuPK(request, queryset, strana):
    #úvodné testy
    pokladna_dir_path  = os.path.join(settings.MEDIA_ROOT,settings.POKLADNA_DIR)
    if not os.path.isdir(pokladna_dir_path):
        os.makedirs(pokladna_dir_path)
    
    #Načítať súbor šablóny
    nazov_objektu = "Pokladničná kniha"  #Presne takto musí byť objekt pomenovaný
    sablona = SystemovySubor.objects.filter(subor_nazov = nazov_objektu)
    if not sablona:
        return messages.ERROR, f"V systéme nie je definovaný súbor '{nazov_objektu}'.", None
    nazov_suboru = sablona[0].subor.file.name 
    workbook = load_workbook(filename=nazov_suboru)
    ws = workbook.active
    ws[f'I3'].value = strana
    riadok = 5
    for item in queryset:
        ws[f'A{riadok}'].value = item.datum_transakcie.strftime("%d. %m. %Y")
        ws[f'C{riadok}'].value = item.popis
        if item.typ_transakcie == TypPokladna.DOTACIA:
            ws[f'G{riadok}'].value = item.suma
        else:
            ws[f'H{riadok}'].value = -item.suma
            rok = re.findall(r"%s-([0-9]*).*"%Pokladna.oznacenie, item.cislo)[0]
            ws[f'B{riadok}'].value = f"{item.cislo_VPD}/{rok}"
        riadok += 1
    ws[f'A55'].value = f"Vygenerované programom DjangoBel {timezone.now().strftime('%d. %m. %Y')}"

    #ulozit
    #Create directory admin.rs_login if necessary
    nazov = 'PK-%02d-%s.xlsx'%(strana,timezone.now().strftime("%d-%m-%Y"))
    opath = os.path.join(settings.POKLADNA_DIR,nazov)
    workbook.save(os.path.join(settings.MEDIA_ROOT,opath))
    mpath = os.path.join(settings.MEDIA_URL,opath)
    msg = format_html(
        'Vytvorená strana pokladničnej knihy bola uložená do súboru {}.',
        mark_safe(f'<a href="{mpath}">{nazov}</a>'),
        )
    return messages.SUCCESS, msg, mpath

def zmazatIndividualneOdmeny(sumarna_odmena):
    qs = OdmenaOprava.objects.filter(typ=OdmenaAleboOprava.ODMENA, cislo__startswith=sumarna_odmena.cislo) 
    for polozka in qs: polozka.delete()
    return len(qs)

def generovatIndividualneOdmeny(sumarna_odmena):
    workbook = load_workbook(filename=sumarna_odmena.subor_odmeny.file.name)
    ws = workbook.active
    #Vyhľadať prvý riadok tabuľky
    riadok = 1
    while ws[f'B{riadok}'].value != "osobné číslo": riadok += 1
    riadok += 1
    # test spravnosti položiek
    aux=riadok
    while ws[f'D{aux}'].value != "spolu":
        suma = ws[f"E{aux}"].value
        if type(suma) == str:
            return [f"Hodnota výšky odmeny v riadku {aux} (a zrejme aj nasledujúcich riadkov) súboru položky {sumarna_odmena.cislo} je vzorec. Súbor upravte tak, aby výška odmeny bola číslo."]
        aux += 1
    pocet=0
    celkova_suma=0
    while ws[f'D{riadok}'].value != "spolu":
        zamestnanec = Zamestnanec.objects.get(cislo_zamestnanca = int(ws[f'B{riadok}'].value))
        suma = float(ws[f"E{riadok}"].value)
        cislo = "%s-%02d"%(sumarna_odmena.cislo,pocet+1)
        try:
            zaznam=OdmenaOprava.objects.get(cislo=cislo)
            zaznam.delete()
        except:
            pass
        odmena = OdmenaOprava (
                cislo = cislo,
                zamestnanec = zamestnanec,
                typ = OdmenaAleboOprava.ODMENA,
                suma = -suma,
                zdroj = sumarna_odmena.zdroj, 
                program = sumarna_odmena.program,
                zakazka = sumarna_odmena.zakazka,
                ekoklas = sumarna_odmena.ekoklas,
                cinnost = sumarna_odmena.cinnost,
                vyplatene_v_obdobi = sumarna_odmena.vyplatene_v_obdobi,
                zdovodnenie = f"Súčasť sumárnej odmeny č. {sumarna_odmena.cislo}"
                )
        odmena.save()
        pocet += 1
        celkova_suma += suma 
        riadok += 1
        pass
    return pocet, celkova_suma


def generovatNepritomnost(sumarna_nepritomnost):
    workbook = load_workbook(filename=sumarna_nepritomnost.subor_nepritomnost.file.name)
    ws = workbook.active
    #ktorý súbor máme?
    if ws["B1"].value == 1 and ws["C1"].value == 2 and ws["D1"].value == 3: #Od Anity
        return generovatNepritomnostAnita(sumarna_nepritomnost.cislo,ws)

def generovatNepritomnostAnita(cislo,ws):
    #Vyhľadať prvý riadok tabuľky
    typy = {
            "D": TypNepritomnosti.DOVOLENKA,
            "D2": TypNepritomnosti.DOVOLENKA2,
            "L": TypNepritomnosti.LEKAR,
            "L/D": TypNepritomnosti.LEKARDOPROVOD,
            "PzV": TypNepritomnosti.PZV,
            "PN": TypNepritomnosti.PN,
            "NV": TypNepritomnosti.NEPLATENE,
            "OČR": TypNepritomnosti.OCR,
            "PV": TypNepritomnosti.PZV,
            "RV": TypNepritomnosti.PZV,
            "SC": TypNepritomnosti.SLUZOBNA,
            "Šk": TypNepritomnosti.SKOLENIE,
            "KZ VS": TypNepritomnosti.PZV
            }
    #ignorovať
    itypy = ["S", "PnD", "SSZ", None]
    #Kontrola tabulky
    prvy = 1
    nriadok = 1
    while ws[f"A{nriadok}"].value: nriadok += 1
    nstlpec = 1
    while ws.cell(row=1, column=nstlpec).value: nstlpec += 1
    for r in range (2,nriadok):
        print(ws[f"A{r}"].value)
        for s in range(2,nstlpec):
            value = ws.cell(row=r, column=s).value
            if not (value in itypy or value in typy):
                return [f"Neznáma položka '{value}' v pozícii ({r},{s})"]
    
    if ws["A1"].value == "November 2022":
        rok = 2022
        mesiac = 11
    elif ws["A1"].value == "December 2022":
        rok = 2022
        mesiac = 12

    zpocet=0  
    npocet=0
    for r in range (2,nriadok):
        aux = ws[f"A{r}"].value
        priezvisko = aux[:aux.index(" ")]
        zamestnanec = Zamestnanec.objects.get(priezvisko=priezvisko)
        s=2
        while s < nstlpec:
            value = ws.cell(row=r, column=s).value 
            if value in ["D", "PN", "NV"]:
                atyp = value
                sstart = s
                while ws.cell(row=r, column=s).value == atyp: s+=1
                nepr = Nepritomnost(
                    cislo = "%s-%02d"%(cislo, npocet+1),
                    zamestnanec = zamestnanec,
                    nepritomnost_typ = typy[atyp],
                    nepritomnost_od = datetime.date(rok, mesiac,sstart-1),
                    nepritomnost_do = datetime.date(rok, mesiac,s-2)
                    )
                print(r, s, nepr.nepritomnost_od, nepr.nepritomnost_do, nepr.nepritomnost_typ)
                s -=1
                npocet += 1
                nepr.save()
            elif value in typy:
                nepr = Nepritomnost(
                    cislo = "%s-%02d"%(cislo, npocet+1),
                    zamestnanec = zamestnanec,
                    nepritomnost_typ = typy[value],
                    nepritomnost_od = datetime.date(rok, mesiac,s-1),
                    nepritomnost_do = datetime.date(rok, mesiac,s-1)
                    )
                npocet += 1
                nepr.save()
                pass
            s+=1
        zpocet += 1
        pass
    return zpocet, npocet

#načítať výšku tarifného platu z aktuálnej tabuľky
class TarifnyPlatTabulky():
    def __init__(self,rok):
        #načítať tabuľky stupnice pre daný rok
        nazov_objektu = "Stupnice platových taríf"  #Presne takto musí byť objekt pomenovaný
        sablona = SystemovySubor.objects.filter(subor_nazov = nazov_objektu)
        if not sablona:
            return messages.ERROR, f"V systéme nie je definovaný súbor '{nazov_objektu}'.", None
        nazov_suboru = sablona[0].subor.file.name 
        workbook = load_workbook(filename=nazov_suboru)
        self.tabulky={}
        for ws_name in workbook.get_sheet_names():
            if not str(rok) in ws_name: continue
            spl = ws_name.replace(" ",".").split(".")
            vdate = datetime.date(int(spl[-1]),int(spl[-2]), int(spl[-3]))
            if not vdate in self.tabulky: self.tabulky[vdate] = {}
            self.tabulky[vdate][spl[0]] = workbook.get_sheet_by_name(ws_name)

    def DatumyValorizacie(self):
        return [k for k in self.tabulky.keys()]

    def TarifnyPlat(self,datum, stupnica, platova_trieda, platovy_stupen):
        #Určiť dátum valorizácie
        for dv in self.DatumyValorizacie():
            if dv > datum: break
            datum_valorizacie = dv
        #Určiť stupnicu
        if stupnica == PlatovaStupnica.ZAKLADNA:
            ws = self.tabulky[datum_valorizacie]['ZS']
            tarifny = ws.cell(row=platovy_stupen+3, column=platova_trieda+2).value
        else:
            ws = self.tabulky[datum_valorizacie]['OS']
            tarifny = ws.cell(row=platovy_stupen+3, column=platova_trieda-3).value
        return tarifny
