# rozne utilitky

# test platnosti IBAN
#https://rosettacode.org/wiki/IBAN#Python
import re, os
from beliana import settings
from django.utils import timezone
from django.contrib import messages
from ipdb import set_trace as trace
 
def valid_iban(iban):
    _country2length = dict(
        AL=28, AD=24, AT=20, AZ=28, BE=16, BH=22, BA=20, BR=29,
        BG=22, CR=21, HR=21, CY=28, CZ=24, DK=18, DO=28, EE=20,
        FO=18, FI=18, FR=27, GE=22, DE=22, GI=23, GR=27, GL=18,
        GT=28, HU=28, IS=26, IE=22, IL=23, IT=27, KZ=20, KW=30,
        LV=21, LB=28, LI=21, LT=20, LU=20, MK=19, MT=31, MR=27,
        MU=30, MC=27, MD=24, ME=22, NL=18, NO=15, PK=24, PS=29,
        PL=28, PT=25, RO=24, SM=27, SA=24, RS=22, SK=24, SI=19,
        ES=24, SE=24, CH=21, TN=24, TR=26, AE=23, GB=22, VG=24 )
 
    # Ensure upper alphanumeric input.
    iban = iban.replace(' ','').replace('\t','')
    if not re.match(r'^[\dA-Z]+$', iban): 
        return False
    # Validate country code against expected length.
    if len(iban) != _country2length[iban[:2]]:
        return False
    # Shift and convert.
    iban = iban[4:] + iban[:4]
    digits = int(''.join(str(int(ch, 36)) for ch in iban)) #BASE 36: 0..9,A..Z -> 0..35
    return digits % 97 == 1

# odstranit diakritiku, špecialne znaky odstranit
def transliterate(text):
    ii= "'’,()[] ?,–_/.-aáäbcčdďeéěfghiíjklľĺmnňoóôöpqrŕřsštťuüúůvwxyýzžAÁÄBCČDĎEÉFGHIÍJKLĽĹMNŇOÓÔPQRŔŘSŠTŤUÜÚŮVWXYÝZŽ0123456789"
    oo= "---------------aaabccddeeefghiijklllmnnoooopqrrrssttuuuuvwxyyzzAAABCCDDEEFGHIIJKLLLMNNOOOPQRRRSSTTUUUUVWXYYZZ0123456789"
    t=""
    for i,c in enumerate(text.strip(" ")):
        t += oo[ii.find(c)]
    return t.replace("-","")

# konvertuje cislo v tvare XY0 do textoveho retazca
def num2text(num):
    s = {
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
        '1': 'desať',
        '2': 'dvadsať',
        '3': 'tridsať',
        '4': 'štyridsať',
        '5': 'päťdesiat',
        '6': 'šesťdesiat',
        '7': 'sedemdesiat',
        '8': 'osemdesiat',
        '9': 'deväťdesiat',
    }
    num=str(num)
    return s[num[0]] + d[num[1]]

def VytvoritAutorskuZmluvu(zmluva):
    #úvodné testy
    if not os.path.isdir(settings.CONTRACTS_DIR):
        return messages.ERROR, f"Chyba pri vytváraní súborov zmluvy: neexistuje priečinok '{settings.CONTRACTS_DIR}'", None
    
    # nacitat sablonu
    lt="&lt;"
    gt="&gt;"
    autor = zmluva.zmluvna_strana
    if not autor.meno or not autor.priezvisko:
        return messages.ERROR, f"Chyba pri vytváraní súborov zmluvy: nie je určené meno alebo priezvisko autora'", None
    mp = f"{autor.titul_pred_menom} {autor.meno} {autor.priezvisko}"
    if autor.titul_za_menom:
        mp = f"{mp}, {autor.titul_za_menom}"
    if not autor.adresa_mesto or not autor.adresa_stat:
        return messages.ERROR, f"Chyba pri vytváraní súborov zmluvy: nie je určené mesto alebo štát autora'", None
    #adresa
    addr = f"{autor.adresa_mesto}, {autor.adresa_stat}"
    if autor.adresa_ulica:
        addr = f"{autor.adresa_ulica}, {addr}"

    #korešpondenčná adresa
    kaddr=""
    if autor.koresp_adresa_mesto:
        kaddr = f"{autor.koresp_adresa_mesto}, {autor.koresp_adresa_stat}"
        if autor.koresp_adresa_ulica:
            kaddr = f"{autor.koresp_adresa_ulica}, {kaddr}"
        if autor.koresp_adresa_institucia:
            kaddr = f"{autor.koresp_adresa_institucia}, {kaddr}"

    # zmluva na podpis s kompletnými údajmi
    try:
        with open(settings.AUTHORS_CONTRACT_TEMPLATE, "r") as f:
            sablona = f.read()
    except:
        return messages.ERROR, f"Chyba pri vytváraní súborov zmluvy: chyba pri čítaní šablóny '{settings.AUTHORS_CONTRACT_TEMPLATE}'", None
    # zmluva pre CRZ

    sablona = sablona.replace(f"{lt}cislozmluvy{gt}", zmluva.cislo_zmluvy)
    sablona = sablona.replace(f"{lt}menopriezvisko{gt}", mp)
    if not autor.odbor:
        return messages.ERROR, f"Chyba pri vytváraní súborov zmluvy: nie je určený odbor autora'", None
    sablona = sablona.replace(f"{lt}odbor{gt}", autor.odbor)
    sablona = sablona.replace(f"{lt}odmenanum{gt}", str(zmluva.honorar_ah).replace(".",","))
    sablona = sablona.replace(f"{lt}odmenatext{gt}", num2text(zmluva.honorar_ah))
    sablona = sablona.replace(f"{lt}dnesnydatum{gt}", timezone.now().strftime("%d. %m. %Y").replace(' 0',' '))
    sablona_crz = sablona

    sablona = sablona.replace(f"{lt}adresa{gt}", addr)
    sablona = sablona.replace(f"{lt}kadresa{gt}", kaddr)
    sablona_crz = sablona_crz.replace(f"{lt}adresa{gt}", "–")
    if not autor.rodne_cislo:
        return messages.ERROR, f"Chyba pri vytváraní súborov zmluvy: nie je určené rodné číslo autora'", None
    sablona = sablona.replace(f"{lt}rodnecislo{gt}", autor.rodne_cislo)
    sablona_crz = sablona_crz.replace(f"{lt}rodnecislo{gt}", "–")
    if not autor.bankovy_kontakt:
        return messages.ERROR, f"Chyba pri vytváraní súborov zmluvy: nie je určený bankový kontakt (napr. ISBN) autora'", None
    sablona = sablona.replace(f"{lt}bankovykontakt{gt}", autor.bankovy_kontakt)
    sablona_crz = sablona_crz.replace(f"{lt}bankovykontakt{gt}", "–")
    if not autor.email:
        return messages.ERROR, f"Chyba pri vytváraní súborov zmluvy: nie je určený email autora'", None
    sablona = sablona.replace(f"{lt}email{gt}", autor.email)
    sablona_crz = sablona_crz.replace(f"{lt}email{gt}", "–")

    if autor.posobisko:
        sablona = sablona.replace(f"{lt}posobisko{gt}", autor.posobisko)
    else:
        sablona = sablona.replace(f"{lt}posobisko{gt}", "")
    sablona = sablona.replace(f"{lt}zdanit{gt}", autor.zdanit)
    sablona = sablona.replace(f"{lt}rezident{gt}", autor.rezident)

    #korešpondenčná adresa
    if autor.koresp_adresa_mesto:
        sablona = sablona.replace(f"{lt}kadresa1{gt}", autor.koresp_adresa_institucia if autor.koresp_adresa_institucia else "")
        sablona = sablona.replace(f"{lt}kadresa2{gt}", autor.koresp_adresa_ulica if autor.koresp_adresa_ulica else "")
        sablona = sablona.replace(f"{lt}kadresa3{gt}", autor.koresp_adresa_mesto if autor.koresp_adresa_mesto else "")
        sablona = sablona.replace(f"{lt}kadresa4{gt}", autor.koresp_adresa_stat if autor.koresp_adresa_stat else "")
    else:
        sablona = sablona.replace(f"{lt}kadresa1{gt}", "")
        sablona = sablona.replace(f"{lt}kadresa2{gt}", autor.adresa_ulica if autor.adresa_ulica else "")
        sablona = sablona.replace(f"{lt}kadresa3{gt}", autor.adresa_mesto if autor.adresa_mesto else "")
        sablona = sablona.replace(f"{lt}kadresa4{gt}", autor.adresa_stat if autor.adresa_stat else "")

    #ulozit
    #Create directory admin.rs_login if necessary
    auxname = f"{autor.rs_login}-{zmluva.cislo_zmluvy.replace('/','-')}"
    odir = os.path.join(settings.CONTRACTS_DIR,auxname)
    if not os.path.isdir(odir):
        os.makedirs(odir)
    vytvorene_subory = []
    fname = f"{auxname}.fodt"
    fname_crz = f"{auxname}-CRZ.fodt"
    for fn, tx in ((fname, sablona), (fname_crz, sablona_crz)): 
        print(fn)
        nazov_zmluvy_log = os.path.join(settings.CONTRACTS_DIR.split("/")[-1],auxname,fn)
        nazov_zmluvy = os.path.join(odir,fn)

        with open(nazov_zmluvy, "w") as f:
            f.write(tx)
        vytvorene_subory.append(nazov_zmluvy_log)
    fnames = ", ".join(vytvorene_subory)
    return messages.SUCCESS, f"Súbory zmluvy {zmluva.cislo_zmluvy} boli úspešne vytvorené ({fnames}).", vytvorene_subory
