# rozne utilitky

import os, locale
from ipdb import set_trace as trace
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from .models import SystemovySubor, PrijataFaktura, AnoNie, Objednavka, PrijataFaktura, Rozhodnutie

def locale_format(d):
    return locale.format('%%0.%df' % (-d.as_tuple().exponent), d, grouping=True)

def VytvoritPlatobyPrikaz(faktura):
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
    text = text.replace(f"{lt}DM{gt}", locale_format(-faktura.suma))    # suma je záporná, o formulári chceme kladné
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
    text = text.replace(f"{lt}CM{gt}", "")
    text = text.replace(f"{lt}predmet_faktury{gt}", faktura.predmet)

    if type(faktura.objednavka_zmluva) == Objednavka:
        text = text.replace(f"{lt}obj_zmluva{gt}", "objednávka")
        text = text.replace(f"{lt}oz_cislo{gt}", faktura.objednavka_zmluva.objednavka.cislo)
        text = text.replace(f"{lt}zo_dna{gt}", faktura.objednavka_zmluva.objednavka.datum_vytvorenia.strftime("%d. %m. %Y"))
        pass
    elif type(faktura.objednavka_zmluva) == PrijataFaktura:
        text = text.replace(f"{lt}obj_zmluva{gt}", "zmluva")
        text = text.replace(f"{lt}oz_cislo{gt}", faktura.objednavka_zmluva.zmluva.cislo)
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
    return messages.SUCCESS, f"Súbory platobného príkazu faktúry {faktura.cislo} bol úspešne vytvorený ({opath}).", opath
