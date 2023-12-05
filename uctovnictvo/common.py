# rozne utilitky

import os, locale
from unidecode import unidecode
from ipdb import set_trace as trace
from django.utils.safestring import mark_safe
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from django.utils.html import format_html
from .models import SystemovySubor, PrijataFaktura, AnoNie, Objednavka, PrijataFaktura, Rozhodnutie, Zmluva
from .models import DoVP, DoPC, DoBPS, Poistovna, TypDochodku, Mena, PravidelnaPlatba, TypPP, TypPokladna, Pokladna
from .models import NajomneFaktura, PrispevokNaRekreaciu, Zamestnanec, OdmenaOprava, OdmenaAleboOprava, TypNepritomnosti, Nepritomnost
from .models import PlatovaStupnica, Stravne, mesiace_num, PlatovyVymer, Mesiace
from .rokydni import mesiace, prac_dni

from openpyxl import load_workbook
from openpyxl.styles import Font, Color, colors, Alignment, PatternFill , numbers
from openpyxl.utils import get_column_letter
from decimal import Decimal

from dateutil.relativedelta import relativedelta

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
    #autor a dátum
    text=re.sub("<dc:creator>[^<]*</dc:creator>", f"<dc:creator>{pouzivatel.get_full_name()}</dc:creator>", text)
    text=re.sub("<dc:date>[^<]*</dc:date>", f"<dc:date>{timezone.now().strftime('%Y-%m-%dT%H:%M:%S.%f')}</dc:date>", text)
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
    #autor a dátum
    text=re.sub("<dc:creator>[^<]*</dc:creator>", f"<dc:creator>{pouzivatel.get_full_name()}</dc:creator>", text)
    text=re.sub("<dc:date>[^<]*</dc:date>", f"<dc:date>{timezone.now().strftime('%Y-%m-%dT%H:%M:%S.%f')}</dc:date>", text)
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
    #autor a dátum
    text=re.sub("<dc:creator>[^<]*</dc:creator>", f"<dc:creator>{pouzivatel.get_full_name()}</dc:creator>", text)
    text=re.sub("<dc:date>[^<]*</dc:date>", f"<dc:date>{timezone.now().strftime('%Y-%m-%dT%H:%M:%S.%f')}</dc:date>", text)
    text = text = text.replace(f"{lt}prevod_cislo{gt}", faktura.cislo)
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
    #autor a dátum
    text=re.sub("<dc:creator>[^<]*</dc:creator>", f"<dc:creator>{pouzivatel.get_full_name()}</dc:creator>", text)
    text=re.sub("<dc:date>[^<]*</dc:date>", f"<dc:date>{timezone.now().strftime('%Y-%m-%dT%H:%M:%S.%f')}</dc:date>", text)
    text = text.replace(f"{lt}nasa_faktura_cislo{gt}", faktura.cislo)
    locale.setlocale(locale.LC_ALL, 'sk_SK.UTF-8')
    if not faktura.suma and not faktura.sumacm:
        return messages.ERROR, "Vytváranie príkazu zlyhalo, lebo nebola zadaná suma v Eur a ani suma v cudzej mene.", None
    if jePF:    #prijatá faktúra môže byť aj v cudzej mene
        sadzbadph = Decimal(faktura.sadzbadph)
        if faktura.mena == Mena.EUR:
            mena = "€"
            suma = -faktura.suma
            #zaklad_dane = 100 *  suma / (100+sadzbadph)
            if faktura.prenosDP == AnoNie.ANO:
                zaklad = 100*suma/(100+sadzbadph)
                text = text.replace(f"{lt}DM{gt}", f"{locale_format(round(zaklad, 2))} {mena}")
                text = text.replace(f"{lt}PDP{gt}", f"{locale_format(round(zaklad*sadzbadph/100,2))} {mena}")
            else:
                text = text.replace(f"{lt}DM{gt}", f"{locale_format(suma)} {mena}")
                text = text.replace(f"{lt}PDP{gt}", "Nie")
            text = text.replace(f"{lt}CM{gt}", "")
        else:
            mena = faktura.mena
            suma = -faktura.sumacm
            #zaklad_dane = 100 *  suma / (100+sadzbadph)
            text = text.replace(f"{lt}DM{gt}", "")
            text = text.replace(f"{lt}CM{gt}", f"{locale_format(suma)} {mena}")     # suma je záporná, vo formulári chceme kladné

        #text = text.replace(f"{lt}sadzbadph{gt}", faktura.sadzbadph)
        #text = text.replace(f"{lt}sumadph{gt}", f"{locale_format(round(suma-zaklad_dane,2))} {mena}")
        text = text.replace(f"{lt}suma1{gt}", f"{locale_format(round((1-faktura.podiel2/100)*suma,2))} {mena}")
        if faktura.podiel2 > 0:
            text = text.replace(f"{lt}suma2{gt}", f"{locale_format(round((faktura.podiel2)*suma/100,2))} {mena}")
        else:
            text = text.replace(f"{lt}suma2{gt}", f"0 {mena}")
    else:   #PravidelnaPlatba, len v EUR
        suma = -faktura.suma
        mena = "€"
        text = text.replace(f"{lt}DM{gt}", f"{locale_format(suma)} €")     # suma je záporná, o formulári chceme kladné
        text = text.replace(f"{lt}CM{gt}", "")
        text = text.replace(f"{lt}suma1{gt}", f"{locale_format(round((1-faktura.podiel2/100)*suma,2))} {mena}")
        if faktura.podiel2 > 0:
            text = text.replace(f"{lt}suma2{gt}", f"{locale_format(round((faktura.podiel2)*suma/100,2))} {mena}")
        else:
            text = text.replace(f"{lt}suma2{gt}", f"0 {mena}")
        text = text.replace(f"{lt}PDP{gt}", "Nie")

    text = text.replace(f"{lt}ekoklas{gt}", faktura.ekoklas.kod)
    text = text.replace(f"{lt}zdroj1{gt}", faktura.zdroj.kod)
    text = text.replace(f"{lt}podiel1{gt}", f"{locale_format(100-faktura.podiel2)}") 
    text = text.replace(f"{lt}zakazka1{gt}", faktura.zakazka.kod)
    if faktura.podiel2 > 0:
        text = text.replace(f"{lt}zakazka2{gt}", faktura.zakazka2.kod)
        text = text.replace(f"{lt}zdroj2{gt}", faktura.zdroj2.kod)
        text = text.replace(f"{lt}podiel2{gt}", f"{locale_format(faktura.podiel2)}") 
    else:
        text = text.replace(f"{lt}zakazka2{gt}", "-")
        text = text.replace(f"{lt}zdroj2{gt}", "-")
        text = text.replace(f"{lt}podiel2{gt}", "0")
    text = text.replace(f"{lt}program{gt}", faktura.program.kod)
    text = text.replace(f"{lt}cinnost{gt}", faktura.cinnost.kod)
    text = text.replace(f"{lt}akt_datum{gt}", timezone.now().strftime("%d. %m. %Y"))
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
    text = text.replace("[[miesto_vykonu]]", dohoda.miesto_vykonu)
    text = text.replace("[[rozvrh_prac_casu]]", dohoda.pracovny_cas)
    text = text.replace("[[datum_od]]", dohoda.datum_od.strftime("%d. %m. %Y"))
    text = text.replace("[[datum_do]]", dohoda.datum_do.strftime("%d. %m. %Y"))
    text = text.replace("[[datum]]", timezone.now().strftime("%d. %m. %Y"))
    text = text.replace("[[zdroj]]", dohoda.zdroj.kod)
    text = text.replace("[[zakazka]]", dohoda.zakazka.kod)
    if dohoda.pomocnik:
        text = text.replace("[[osobne_pomoc]]", "za pomoci rod. príslušníkov ")
        text = text.replace("[[pomocnik]]", dohoda.pomocnik)
    else:
        text = text.replace("[[osobne_pomoc]]", "osobne")
        text = text.replace("[[pomocnik]]", "")

    # vložiť údaje DoVP
    if type(dohoda) == DoVP:
        text = text.replace("[[typ_dohody]]", "o vykonaní práce")
        text = text.replace("[[zakony]]", "§ 223 – § 225 a § 226")
        text = text.replace("[[odmena]]", f"{dohoda.odmena_celkom} Eur")
        text = text.replace("[[rozsah_prace_cas]]", f"{dohoda.hod_celkom} hodín")
        text = text.replace("[[doba_text]]", f"v ktorej sa má pracovná úloha vykonať")
        text = text.replace("[[odmena_text]]", f"odmena za vykonanie celej prac. úlohy je")
        text = text.replace("[[rozsah_text]]", f"Predpokladaný rozsah práce (pracovnej úlohy)")
        text = text.replace("[[vyplatny_termin]]", dohoda.datum_do.strftime("%m/%Y")) 
        text = text.replace("[[dohodnuty_predpokladany]]", "Predpokladaný")
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
        text = text.replace("[[odmena]]", f"{dohoda.odmena_mesacne} Eur / mesiac")
        text = text.replace("[[rozsah_prace_cas]]", f"{dohoda.hod_mesacne} hodín / mesiac")
        text = text.replace("[[dohodnuty_predpokladany]]", "Predpokladaný")
        text = text.replace("[[doba_text]]", f"na ktorú sa dohoda uzatvára")
        text = text.replace("[[rozsah_text]]", f"Predpokladaný rozsah práce")
        text = text.replace("[[odmena_text]]", "")
        text = dohoda_skryt_sekcie(text, "DoPC")
        if dohodar.poberatel_doch == AnoNie.NIE:
            text = dohoda_skryt_sekciu(text, 'text:name="DoPC_DoVP_vyhlasenie"')
    # vložiť údaje DoBPS
    elif type(dohoda) == DoBPS:
        text = text.replace("[[typ_dohody]]", "o brigádnickej práci študentov")
        text = text.replace("[[zakony]]", "§ 223 – § 225, § 227 a § 228")
        text = text.replace("[[odmena]]", f"{dohoda.odmena_mesacne} Eur mesačne")
        text = text.replace("[[rozsah_prace_cas]]", "asdf")
        text = text.replace("[[dohodnuty_predpokladany]]", "Dohodnutý")
        text = text.replace("[[doba_text]]", f"na ktorú sa dohoda uzatvára")
        text = text.replace("[[rozsah_text]]", f"Dohodnutý rozsah pracovného času")
        text = text.replace("[[odmena_text]]", "")
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
    pocet_riadkov = 18 # pri zmene zmeniť aj models.Objednavka.clean.pocet_riadkov
    add_sum = True  # či s má do posledného riadka vložiť súčet
    for rr, polozka in enumerate(objednavka.objednane_polozky.split("\n")):
        riadok = prvy_riadok+rr
        prvky = polozka.split(";")
        if len(prvky) == 2:  #zlúčiť bunky
            obj.merge_cells(f'B{riadok}:G{riadok}')
            obj[f"B{riadok}"].value = prvky[0]
            obj.cell(row=riadok, column=2+6).value = prvky[1]
            add_sum = False
        elif len(prvky) == 5:
            obj.cell(row=riadok, column=2+0).value = prvky[0]
            obj.cell(row=riadok, column=2+1).value = prvky[1]
            val2 = float(prvky[2].strip().replace(",","."))
            obj.cell(row=riadok, column=2+2).value = val2
            obj.cell(row=riadok, column=2+2).number_format= "0.00"
            val3 = float(prvky[3].strip().replace(",","."))
            obj.cell(row=riadok, column=2+3).value = val3
            obj.cell(row=riadok, column=2+4).number_format= "0.00"
            obj.cell(row=riadok, column=2+6).value = prvky[4]
            #nefunguje, ktovie prečo
            #
            if objednavka.dodavatel.s_danou==AnoNie.ANO:
                #obj[f'G{riadok}'] = f'=IF(ISBLANK(D{riadok});" ";D{riadok}*E{riadok})'
                obj[f'G{riadok}'] = val2*val3*DPH
            else:
                obj[f'F{riadok}'] = val2*val3
            add_sum = True
        else:
            return messages.ERROR, f"Riadok {rr+1} zoznamu položiek má nesprávny počet polí (počet polí {len(prvky)}, počet bodkočiarok {len(prvky) -1}). Text upravte tak, aby mal práve 5 poli (4 bodkočiarky) alebo 2 polia (1 bodkočiarka). Všetky riadky musia byť členené na polia rovnako.", None

        if add_sum: 
            if objednavka.dodavatel.s_danou==AnoNie.ANO:
                obj[f'G{prvy_riadok+pocet_riadkov}'] = f"=SUM(G{prvy_riadok}:G{prvy_riadok+pocet_riadkov-1})"
            else:
                obj[f'F{prvy_riadok+pocet_riadkov}'] = f"=SUM(F{prvy_riadok}:F{prvy_riadok+pocet_riadkov-1})"


    if objednavka.termin_dodania:
        obj[f"A{prvy_riadok+pocet_riadkov+2}"].value = obj[f"A{prvy_riadok+pocet_riadkov+2}"].value.replace("[[termin_dodania]]", objednavka.termin_dodania)
    else:
        obj[f"A{prvy_riadok+pocet_riadkov+2}"].value = obj[f"A{prvy_riadok+pocet_riadkov+2}"].value.replace("[[termin_dodania]]", "")
    if not objednavka.datum_vytvorenia:
        return messages.ERROR, "Vytváranie súboru objednávky zlyhalo, lebo objednávka nemá zadaný dátum vytvorenia.", None
    obj[f"A{prvy_riadok+pocet_riadkov+4}"].value = obj[f"A{prvy_riadok+pocet_riadkov+4}"].value.replace("[[datum]]", objednavka.datum_vytvorenia.strftime("%d. %m. %Y"))
  
    kl = workbook["Finančná kontrola"]
    kl["A1"].value = kl["A1"].value.replace("[[cislo]]", objednavka.cislo)
    kl["A1"].value = kl["A1"].value.replace("[[datum]]", objednavka.datum_vytvorenia.strftime("%d. %m. %Y"))

    #ulozit
    #Create directory admin.rs_login if necessary
    nazov = f'{objednavka.cislo}-{objednavka.dodavatel.nazov.replace(" ","").replace(".","").replace(",","-")}.xlsx'
    opath = os.path.join(settings.OBJEDNAVKY_DIR,nazov)
    workbook.save(os.path.join(settings.MEDIA_ROOT,opath))
    return messages.SUCCESS, f"Súbor objednávky {objednavka.cislo} bol úspešne vytvorený ({opath}). Súbor dajte na podpis.", opath

def VytvoritSuborPD(vpd):
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
    obj = workbook["PD"]
    if vpd.typ_transakcie == TypPokladna.PPD:
        obj["G1"].value = "PRÍJMOVÝ"
        obj["B7"].value = "Prijaté od"
        obj["G14"].value = "Dal - účet"

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

    if vpd.typ_transakcie == TypPokladna.PPD:
        nazov = f'PPD-{cislovpd}.xlsx'.replace("/","-")
    else:
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
        elif item.typ_transakcie == TypPokladna.VPD:
            ws[f'H{riadok}'].value = -item.suma
            rok = re.findall(r"%s-([0-9]*).*"%Pokladna.oznacenie, item.cislo)[0]
            ws[f'B{riadok}'].value = f"VPD {item.cislo_VPD}/{rok}"
        else:
            ws[f'G{riadok}'].value = item.suma
            rok = re.findall(r"%s-([0-9]*).*"%Pokladna.oznacenie, item.cislo)[0]
            ws[f'B{riadok}'].value = f"PPD {item.cislo_VPD}/{rok}"
        riadok += 1
    ws[f'A54'].value = f"Vygenerované programom DjangoBel {timezone.now().strftime('%d. %m. %Y')}"

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
    else:
        return [f"Neznámy súbor. Údaje o neprítomnosti sa načítajú z prvého hárka"]

def generovatNepritomnostAnita(cislo,ws):
    def check_value(value):
        if not value: return None
        svalue = value.replace("  "," ").split(" ")
        if not (svalue[0] in itypy or svalue[0] in typy):
            return f"Neznáma položka '{value}'";
        if svalue[0] == "D" and len(svalue) > 1:
            return f"Chybná položka 'D'. Mǒže byť len 'D' alebo 'D2' ale nie '{value}'."
        #Všetko OK
        return None
    #Typy neprítomnosti
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
            "KZ VS": TypNepritomnosti.PZV,
            "POH": TypNepritomnosti.PZV
            }
    #ignorovať
    itypy = ["S", "PnD", "SSZ", None]
    # rok a mesiac
    a1split = ws["A1"].value.lower().replace("  ", " ").split(" ")
    if not len(a1split) == 2:
        return [f"V bunke A1 sa nenachádza údaj 'Mesiac rok'."]
    if not a1split[0] in mesiace:
        return [f"V bunke A1 je nesprávny údaj 'Mesiac rok'."]
    mesiac = mesiace.index(a1split[0])+1
    rok = int(a1split[1])

    #Určenie počtu riadkov
    prvy = 1
    nriadok = 1
    while ws[f"A{nriadok}"].value: nriadok += 1

    #Kontrola tabulky
    nstlpec = 1
    while ws.cell(row=1, column=nstlpec).value: nstlpec += 1
    for r in range (2,nriadok):
        print(ws[f"A{r}"].value)
        for s in range(2,nstlpec):
            rslt = check_value(ws.cell(row=r, column=s).value)
            if rslt:
                trace()
                pass
                return [f"Chyba v pozícii ({r},{s}): {rslt}"]
    zpocet=0  
    npocet=0
    for r in range (2,nriadok):
        aux = ws[f"A{r}"].value
        priezvisko = aux[:aux.index(" ")]
        zamestnanec = Zamestnanec.objects.get(priezvisko=priezvisko)
        s=2
        while s < nstlpec:
            value = ws.cell(row=r, column=s).value
            if value:
                scell = value.replace("  "," ").split(" ")
                ntyp = scell[0]
            else:
                ntyp = None
            if ntyp in ["D", "PN", "NV", "OČR"]:  #intervalové neprítomnosti
                sstart = s
                while ws.cell(row=r, column=s).value == ntyp: s+=1
                nepr = Nepritomnost(
                    cislo = "%s-%02d"%(cislo, npocet+1),
                    zamestnanec = zamestnanec,
                    nepritomnost_typ = typy[ntyp],
                    nepritomnost_od = datetime.date(rok, mesiac,sstart-1),
                    nepritomnost_do = datetime.date(rok, mesiac,s-2)
                    )
                print(r, s, nepr.nepritomnost_od, nepr.nepritomnost_do, nepr.nepritomnost_typ)
                s -=1
                npocet += 1
                nepr.save()
            elif ntyp in typy: #Jednodňové neprítomnosti
                nepr = Nepritomnost(
                    cislo = "%s-%02d"%(cislo, npocet+1),
                    zamestnanec = zamestnanec,
                    nepritomnost_typ = typy[ntyp],
                    nepritomnost_od = datetime.date(rok, mesiac,s-1),
                    nepritomnost_do = datetime.date(rok, mesiac,s-1)
                    )
                if len(scell) > 1:
                    nepr.dlzka_nepritomnosti = Decimal(float(scell[1].replace(",",".")))
                npocet += 1
                nepr.save()
                pass

            s+=1
        zpocet += 1
        pass
    return zpocet, npocet

def generovatStravne(polozka):
    #načítať tabuľky stupnice pre daný rok
    nazov_objektu = "Šablóna stravné"  #Presne takto musí byť objekt pomenovaný
    sablona = SystemovySubor.objects.filter(subor_nazov = nazov_objektu)
    if not sablona:
        return [f"V systéme nie je definovaný súbor '{nazov_objektu}'."]
    nazov_suboru = sablona[0].subor.file.name 
    workbook = load_workbook(filename=nazov_suboru)
    #testovať správnosť
    for harok in ['Sadzba', 'Príspevky', 'Zrážky']:
        if not harok in workbook.sheetnames:
            return [f"Súbor '{nazov_objektu}' nemá hárok {harok}"]
    #Načítať sadzby
    sadzba = {}
    #testovať správnosť
    ws_sadzba = workbook["Sadzba"]
    sadzba_cols = ["Dátum od", "Sadzba EnÚ", "Sadzba SF"]
    sadzba_hdr = [cell.value for cell in  list(ws_sadzba)[0]]
    if len(set(sadzba_cols).intersection(set(sadzba_hdr))) != 3:
        return [f"Hárok 'Sadzba' nemá všetky požadované stĺpce: {','.join(sadzba_cols)}"]

    #Dátumy platnosti jednotlivých sadzieb príspevkov
    sadzby={}
    for row in list(ws_sadzba)[1:]:
        if row[0].value:
            sadzby[row[0].value] = [row[1].value, row[2].value]

    #Nájsť správnu sadzbu
    rok = polozka.cislo.split("-")[1]
    if polozka.typ_zoznamu == Stravne.PRISPEVKY:
        # Príspevky sú za nasledujúci mesiac
        if mesiace_num[polozka.za_mesiac][0] == 12:
            mesiac_prispevku = datetime.date(int(rok)+1, 1, 1) 
        else:
            mesiac_prispevku = datetime.date(int(rok), mesiace_num[polozka.za_mesiac][0]+1, 1) 
    else: #zrážky
        mesiac_prispevku = datetime.date(int(rok), mesiace_num[polozka.za_mesiac][0], 1) 
    prispevok_sadzba = None
    for den in [*sadzby][::-1]: #reverzne usporiadany zoznam dni v sadzby
        dden = datetime.date(den.year,den.month,den.day)
        if dden <= mesiac_prispevku:
            prispevok_sadzba = sadzby[den]
            break

    #mesiac od - do
    od = mesiac_prispevku
    next_month = od + relativedelta(months=1, day=1)  # 1. deň nasl. mesiaca
    do=next_month - relativedelta(days=1) # koniec mesiaca

    #Nájsť zamestnancov zamestnaných v danom mesiaci, t.j.
    #Najst platové výmery aktívne v danom mesiaci
    qs = PlatovyVymer.objects.filter(datum_od__lte=mesiac_prispevku)
    qs1 = qs.exclude(datum_do__lt=mesiac_prispevku)
    #zoznam výmerov zoradený podľa priezviska
    vymer_list = sorted([*qs1], key=lambda x: unidecode(x.zamestnanec.priezvisko))
 
    #Vyplniť hárok
    suma_enu = 0
    suma_sf = 0
    n_zam = 0
    msg = ""
    bez_prispevku = []  #zamestnanci, ktorým sa nevypláca príspevok (pre message)
    nepritomny_mesiac = []  #zamestnanci, ktorí boli meprítomní celý mesiac ale príspevol sa vypláca

    kryci_list =  workbook["Krycí list"]
    if polozka.typ_zoznamu == Stravne.PRISPEVKY:
        ws = workbook["Príspevky"] 
        #určiť mesiac(text)
        za_mesiac = "-"
        za_rok = mesiac_prispevku.year
        for mn in mesiace_num:  #Nájsť meno mesiaca
            if mesiace_num[mn][0] == mesiac_prispevku.month:
                za_mesiac=mesiace_num[mn][1]
        ws.cell(row=2, column=1).value = f"na mesiac/rok: {za_mesiac}/{za_rok}"
        nn=6    #prvý riadok
        #Príspevok vyplácať za každý mesiac, pokiaľ nie je splnená podmienka vymer.zamestnanec.bez_stravneho_od <= mesiac_prispevku
        #vymer.zamestnanec.bez_stravneho_od sa nastavuje pred výpočtom príspevku a ručí po výpočte zrážok
        #Pokiaľ zamestnanec neohlásene ukončí neprítomnosť (napr. 15. príde do práce a povie, že už je zdravý), 
        # tak sa ukončí neprítomnosť, ktorá súvisí so zamestnanec.bez_stravneho_od. Keďže však zamestnanec.bez_stravneho_od je stále 
        # nastavené zrážka za vypočíta za dni v meziaci PO ukončení neprítomnosti s opačným znamienkom.
        #
        for vymer in vymer_list:    #výmery všetkých zamestnancov aktívne v aktuálnom mesiaci 
            #bez stavného kvôli dlhodobej neprítomnosti?
            ws.cell(row=nn, column=1).value = n_zam+1
            ws.cell(row=nn, column=2).value = vymer.zamestnanec.cislo_zamestnanca
            ws.cell(row=nn, column=3).value = vymer.zamestnanec.priezviskomeno(",")
            # Počet pracovných dní v aktuálnom mesiaci
            pocet_prac_dni = prac_dni(od, do, ppd=0 if vymer.uvazok > 37 else 3)
            #dlhodobá neprítomnost
            #bez_stravneho_od brat do úvahy len vtedy, keď aktuálne známa neprítomnost je celý mesiac 
            nepritomnost = vymer.nepritomnost_za_mesiac(mesiac_prispevku, pre_stravne = True)
            pdni, ddov, ddov2, dosob, dnepl, dpn1, dpn2, docr = nepritomnost
            if dnepl == pocet_prac_dni: #nutná podmienka nevyplácania
                if vymer.zamestnanec.nevyplacat_stravne(mesiac_prispevku):
                    bez_prispevku.append(vymer.zamestnanec)
                    pocet_prac_dni = 0
                else:
                    nepritomny_mesiac.append(vymer.zamestnanec)

            ws.cell(row=nn, column=4).value = pocet_prac_dni
            ws.cell(row=nn, column=5).value = pocet_prac_dni*prispevok_sadzba[0]
            suma_enu += pocet_prac_dni*prispevok_sadzba[0]
            ws.cell(row=nn, column=6).value = pocet_prac_dni*prispevok_sadzba[1]
            ws.cell(row=nn, column=7).value = f"=E{nn}+F{nn}"
            suma_sf += pocet_prac_dni*prispevok_sadzba[1]
            nn += 1
            n_zam += 1
            pass
        ws.cell(row=42, column=3).value = datetime.date.today().strftime('%d. %m. %Y')
        workbook.remove_sheet(workbook.get_sheet_by_name("Sadzba"))
        workbook.remove_sheet(workbook.get_sheet_by_name("Zrážky"))
        kryci_list.cell(row=2, column=1).value = f"Príspevok na stravné za mesiac {za_mesiac} {za_rok}"
        kryci_list.cell(row=3, column=1).value = datetime.date.today().strftime('%d. %m. %Y')
    else:   #zrážky
        za_mesiac = polozka.za_mesiac
        za_rok = mesiac_prispevku.year
        ws = workbook["Zrážky"] 
        ws.cell(row=2, column=1).value = f"za mesiac/rok: {Mesiace(polozka.za_mesiac).label}/{rok}"
        nn=6    #prvý riadok
        for vymer in vymer_list:
            # Počet pracovných dní v aktuálnom mesiaci
            pocet_prac_dni = prac_dni(od, do, ppd=0 if vymer.uvazok > 37 else 3)
            nepritomnost = vymer.nepritomnost_za_mesiac(mesiac_prispevku, pre_stravne = True)
            pdni, ddov, ddov2, dosob, dnepl, dpn1, dpn2, docr = nepritomnost
            if dnepl == pocet_prac_dni and vymer.zamestnanec.nevyplacat_stravne(mesiac_prispevku):
                bez_prispevku.append(vymer.zamestnanec)
                pocet_dni = 0
            else:
                #Tu definovať, za čo sú zrážky
                pocet_dni = ddov + ddov2 + dosob + dnepl + docr #dpn1 a dpn2 sa neráta, je zahrnuté v dnepl

            ws.cell(row=nn, column=1).value = n_zam+1
            ws.cell(row=nn, column=2).value = vymer.zamestnanec.cislo_zamestnanca
            ws.cell(row=nn, column=3).value = vymer.zamestnanec.priezviskomeno(",")
            ws.cell(row=nn, column=4).value = pocet_dni
            if pocet_dni:
                ws.cell(row=nn, column=5).value = pocet_dni*(prispevok_sadzba[0]+prispevok_sadzba[1])
            else:
                ws.cell(row=nn, column=5).value = "-"
            suma_enu += pocet_dni*prispevok_sadzba[0]
            suma_sf += pocet_dni*prispevok_sadzba[1]
            nn += 1
            n_zam += 1
            pass
        ws.cell(row=43, column=4).value = prispevok_sadzba[0]
        ws.cell(row=43, column=5).value = suma_enu
        ws.cell(row=44, column=4).value = prispevok_sadzba[1]
        ws.cell(row=44, column=5).value = suma_sf
        ws.cell(row=47, column=2).value = datetime.date.today().strftime('%d. %m. %Y')
        workbook.remove_sheet(workbook.get_sheet_by_name("Sadzba"))
        workbook.remove_sheet(workbook.get_sheet_by_name("Príspevky"))
        kryci_list.cell(row=2, column=1).value = f"Zrážky za prekážky v práci za mesiac {za_mesiac} {za_rok}"
        kryci_list.cell(row=3, column=1).value = datetime.date.today().strftime('%d. %m. %Y')
        pass
    #Aktualizovať hárok Krycí list
    
    #Save the workbook
    if nepritomny_mesiac:
        mmm = f"{msg}<br />Zamestnanci, ktorí neodpracovali/neodpracujú celý mesiac {mesiac_prispevku.month}/{mesiac_prispevku.year}, avšak ich príspevok na stravné bude v súbore uvedený:"
        for zam in nepritomny_mesiac:
            mmm = f"{mmm}: <strong>{zam}</strong>"
        msg = f"{mmm}"
    if bez_prispevku:
        mmm = f"{msg}<br />Zamestnanci bez príspevku/zrážky z dôvodu dlhodobej neprítomnosti:"
        for zam in bez_prispevku:
            mmm = f"{mmm}: <strong>{zam}</strong>"
        msg = f"{mmm}"

    if bez_prispevku or nepritomny_mesiac:
        msg = f"{msg}<br />"
        msg = f"{msg}.<br />Ak treba, dlhodobú neprítomnosť zamestnancov upravte (vyplňte pole <em>Zamestnanec > Bez stravného od / do</em>) a súbor s príspevkmi/zrážkami vygenerujte znovu." 
    nazov = f"Stravne-{polozka.typ_zoznamu}-{za_rok}-{za_mesiac}.xlsx"
    opath = os.path.join(settings.STRAVNE_DIR,nazov)
    workbook.save(os.path.join(settings.MEDIA_ROOT,opath))
    return float(suma_enu), float(suma_sf), n_zam, msg, opath

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
        #posledná platová tabuľka za predchádzajúce roky
        predch_datum = datetime.date(2000,1,1)
        #všetky relevantné tabuľky
        relevantne_datumy = []
        for ws_name in workbook.get_sheet_names():
            if not ws_name[:2] in ("ZS", "OS"): continue
            spl = ws_name.replace(" ",".").split(".")
            vdate = datetime.date(int(spl[-1]),int(spl[-2]), int(spl[-3]))
            #posledná za predchádzajúce
            if vdate < datetime.date(rok, 1, 1):
                predch_datum = max(vdate, predch_datum)
            #všetky aktuálne
            if str(rok) in ws_name:
                relevantne_datumy.append(vdate)
        if predch_datum > datetime.date(2000,1,1):
            relevantne_datumy.append(predch_datum)

        #platové tabuľky za 'rok'
        for ws_name in workbook.get_sheet_names():
            if not ws_name[:2] in ("ZS", "OS"): continue
            spl = ws_name.replace(" ",".").split(".")
            vdate = datetime.date(int(spl[-1]),int(spl[-2]), int(spl[-3]))
            if vdate in relevantne_datumy:
                if not vdate in self.tabulky:
                    self.tabulky[vdate] = {}
                self.tabulky[vdate][spl[0]] = workbook.get_sheet_by_name(ws_name)
        #ak za 'rok' nie je žiadna valorizácia zadaná
        pass

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
