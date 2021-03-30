# rozne utilitky

# test platnosti IBAN
#https://rosettacode.org/wiki/IBAN#Python
import re, os
from beliana import settings
from django.utils import timezone
from django.contrib import messages
 
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

# odstranit diakritiku, špecialne znaky zmenit na -
def transliterate(text):
    ii= "'’,()[] ?,–_/.-aáäbcčdďeéěfghiíjklľĺmnňoóôöpqrŕřsštťuüúůvwxyýzžAÁÄBCČDĎEÉFGHIÍJKLĽĹMNŇOÓÔPQRŔŘSŠTŤUÜÚŮVWXYÝZŽ0123456789"
    oo= "-------__--_/.-aaabccddeeefghiijklllmnnoooopqrrrssttuuuuvwxyyzzAAABCCDDEEFGHIIJKLLLMNNOOOPQRRRSSTTUUUUVWXYYZZ0123456789"
    t=""
    for i,c in enumerate(text.strip(" ")):
        t += oo[ii.find(c)]
    return t

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

def VytvoritAutorskuZmluvu(autor, cislozmluvy, odmena):
    # nacitat sablonu
    lt="&lt;"
    gt="&gt;"
    with open(settings.SABLONA_AUTORSKA_ZMLUVA, "r") as f:
        sablona = f.read()
    sablona = sablona.replace(f"{lt}cislozmluvy{gt}", cislozmluvy)
    mp = f"{autor.titul_pred_menom} {autor.meno} {autor.priezvisko}"
    if autor.titul_za_menom:
        mp = f"{mp}, {autor.titul_za_menom}"
    sablona = sablona.replace(f"{lt}menopriezvisko{gt}", mp)
    addr = f"{autor.adresa_mesto}, {autor.adresa_stat}"
    if autor.adresa_ulica:
        addr = f"{autor.adresa_ulica}, {addr}"
    sablona = sablona.replace(f"{lt}adresa{gt}", addr)
    sablona = sablona.replace(f"{lt}rodnecislo{gt}", autor.rodne_cislo)
    sablona = sablona.replace(f"{lt}bankovykontakt{gt}", autor.bankovy_kontakt)
    sablona = sablona.replace(f"{lt}email{gt}", autor.email)
    sablona = sablona.replace(f"{lt}odbor{gt}", autor.odbor)
    sablona = sablona.replace(f"{lt}odmenanum{gt}", odmena)
    sablona = sablona.replace(f"{lt}odmenatext{gt}", num2text(odmena))
    sablona = sablona.replace(f"{lt}dnesnydatum{gt}", timezone.now().strftime("%d. %m. %Y").replace(' 0',' '))

    #ulozit
    fname = f"{autor.rs_login}-{cislozmluvy.replace('/','-')}.fodt"
    nazov_zmluvy_log = os.path.join(settings.ZMLUVY_DIR.split("/")[-1],autor.rs_login,fname)

    if not os.path.isdir(settings.ZMLUVY_DIR):
        return messages.ERROR, f"Chyba pri vytváraní súboru '{nazov_zmluvy_log}': neexistuje priečinok '{settings.ZMLUVY_DIR}'"
    
    #Create directory admin.rs_login if necessary
    odir = os.path.join(settings.ZMLUVY_DIR,autor.rs_login)
    nazov_zmluvy = os.path.join(odir,fname)
    if not os.path.isdir(odir):
        os.makedirs(odir)

    with open(nazov_zmluvy, "w") as f:
        f.write(sablona)
    return messages.SUCCESS, f"Zmluva '{nazov_zmluvy_log}' bola úspešne vytvorená"
