# rozne utilitky

import os, locale
from ipdb import set_trace as trace
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from .models import SystemovySubor, PrijataFaktura, AnoNie, Objednavka, PrijataFaktura, Rozhodnutie, Zmluva
from .models import DoVP, DoPC, Poistovna, TypDochodku, Mena

from openpyxl import load_workbook
from openpyxl.styles import Font, Color, colors, Alignment, PatternFill , numbers
from openpyxl.utils import get_column_letter

import datetime, calendar

def leapdays(datefrom, dateto):
    yearfrom = datefrom.year
    if datefrom >= datetime.date(yearfrom, 3, 1): yearfrom += 1
    yearto = dateto.year
    if dateto >= datetime.date(yearto, 3, 1): yearto += 1
    return calendar.leapdays(yearfrom, yearto)

def locale_format(d):
    return locale.format('%%0.%df' % (-d.as_tuple().exponent), d, grouping=True)

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
            
def VytvoritPlatobnyPrikaz(faktura):
    #úvodné testy
    if not os.path.isdir(settings.PLATOBNE_PRIKAZY_DIR):
        os.makedirs(settings.PLATOBNE_PRIKAZY_DIR)
    
    # nacitat sablonu
    lt="[["
    gt="]]"

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
    if faktura.mena == Mena.EUR:
        text = text.replace(f"{lt}DM{gt}", f"{locale_format(-faktura.suma)} €")     # suma je záporná, o formulári chceme kladné
        text = text.replace(f"{lt}CM{gt}", "")
    else:
        text = text.replace(f"{lt}CM{gt}", f"{locale_format(-faktura.suma)} {faktura.mena}")    # suma je záporná, o formulári chceme kladné
        text = text.replace(f"{lt}DM{gt}", "")
    text = text.replace(f"{lt}dodavatel{gt}", faktura.objednavka_zmluva.dodavatel.nazov)
    text = text.replace(f"{lt}adresa1{gt}", faktura.objednavka_zmluva.dodavatel.adresa_ulica)
    text = text.replace(f"{lt}adresa2{gt}", faktura.objednavka_zmluva.dodavatel.adresa_mesto)
    text = text.replace(f"{lt}adresa3{gt}", faktura.objednavka_zmluva.dodavatel.adresa_stat)
    text = text.replace(f"{lt}dodavatel_faktura{gt}", 
            faktura.dcislo if faktura.dcislo else "")
    text = text.replace(f"{lt}doslo_dna{gt}", 
            faktura.doslo_datum.strftime("%d. %m. %Y") if faktura.doslo_datum else "" )
    text = text.replace(f"{lt}datum_splatnosti{gt}", 
            faktura.splatnost_datum.strftime("%d. %m. %Y") if faktura.splatnost_datum else "")
    text = text.replace(f"{lt}predmet_faktury{gt}", faktura.predmet)

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
        pass

    text = text.replace(f"{lt}ekoklas{gt}", faktura.ekoklas.kod)
    text = text.replace(f"{lt}zdroj{gt}", faktura.zdroj.kod)
    if faktura.zdroj.kod == '111':
        text = text.replace(f"{lt}dph_neuctovat{gt}", "DPH neúčtovať")
    else:
        text = text.replace(f"{lt}dph_neuctovat{gt}", "")
    text = text.replace(f"{lt}program{gt}", faktura.program.kod)
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
    return messages.SUCCESS, f"Súbor platobného príkazu faktúry {faktura.cislo} bol úspešne vytvorený ({opath}).", opath


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
        text = text.replace("[[ztp]]", AnoNie(dohodar.ztp).label)

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
