import csv, re
from django.core.management import BaseCommand, CommandError
from django.utils import timezone
from ipdb import set_trace as trace
from datetime import date, timedelta
from simple_history.utils import update_change_reason

from uctovnictvo.models import ZamestnanecDohodar, Zamestnanec, Dohodar, DoVP, DoPC, PlatovyVymer
from uctovnictvo.models import Zdroj, Program, TypZakazky, EkonomickaKlasifikacia
from uctovnictvo.rokydni import datum_postupu, vypocet_prax, vypocet_zamestnanie 

class Command(BaseCommand):
    help = 'Načítať údaje o zamestnancoch a dohodaroch'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help="csv súbor s dátami o zamestnancoch a dohodároch")

    def read_data(self, path):
        hdr = []
        data ={}
        with open(path, 'rt') as f:
            reader = csv.reader(f, dialect='excel')
            for row in reader:
                if not hdr:
                    hdr = row[1:]
                    continue
                rrr = [r.replace("\xa0","") for r in row]
                data[rrr[0]] = rrr[1:]
        return hdr, data

    def handle(self, *args, **kwargs):
        path = kwargs['path']
        hdr, zamestnanci = self.read_data(path)
        nn={}
        for n, val in enumerate(hdr):
            nn[val]=n
        zd_set = ZamestnanecDohodar.objects.filter()

        for zd in zd_set:
            print(zd)
            if zd.priezvisko in zamestnanci:
                osoba = Zamestnanec()
            else:
                osoba = Dohodar()
            osoba.bankovy_kontakt = zd.bankovy_kontakt
            osoba.adresa_ulica = zd.adresa_ulica
            osoba.adresa_mesto = zd.adresa_mesto
            osoba.adresa_stat = zd.adresa_stat
            osoba.datum_aktualizacie = zd.datum_aktualizacie
            osoba.email = zd.email
            osoba.titul_pred_menom = zd.titul_pred_menom
            osoba.meno = zd.meno
            osoba.priezvisko = zd.priezvisko
            osoba.titul_za_menom = zd.titul_za_menom
            osoba.rodne_cislo = zd.rodne_cislo
            osoba.poznamka = zd.poznamka
            osoba.datum_nar = zd.datum_nar
            osoba.rod_priezvisko = zd.rod_priezvisko
            osoba.miesto_nar = zd.miesto_nar
            osoba.st_prislusnost = zd.st_prislusnost
            osoba.stav = zd.stav
            osoba.poberatel_doch = zd.poberatel_doch
            osoba.typ_doch = zd.typ_doch
            osoba.datum_doch = zd.datum_doch
            osoba.ztp = zd.ztp
            osoba.datum_ztp = zd.datum_ztp
            osoba.poistovna = zd.poistovna
            osoba.cop = zd.cop
            if zd.priezvisko in zamestnanci:
                osoba.cislo_zamestnanca = zamestnanci[zd.priezvisko][0]
                osoba.zapocitane_roky = int(zamestnanci[zd.priezvisko][1])
                osoba.zapocitane_dni = int(zamestnanci[zd.priezvisko][2])
                dd, mm, rr =re.findall(r"([0-9]*)[.]([0-9]*)[.]([0-9]*)", zamestnanci[zd.priezvisko][3])[0]
                osoba.zamestnanie_od = date(int(rr),int(mm),int(dd)) 
            osoba.save()
            # vymeniť povodny zmluvna_strana za novy 
            dovp_set = DoVP.objects.filter(zmluvna_strana=zd)
            for dd in dovp_set:
                if type(dd.zmluvna_strana)!=ZamestnanecDohodar:
                    continue
                dd.zmluvna_strana = osoba
                dd.save()
 
            dopc_set = DoPC.objects.filter(zmluvna_strana=zd)
            for dd in dopc_set:
                if type(dd.zmluvna_strana)!=ZamestnanecDohodar:
                    continue
                dd.zmluvna_strana = osoba
                dd.save()
            # zmazať, už nepotrebujeme
            zd.delete()

            #vytvoriť PlatovyVymer pre zamestnancov
            if zd.priezvisko in zamestnanci:
                #trieda1 4	stupen1 5	uvazok1 6	platnyod1 7	    tarifny1 8	osobny1 9	riadenie1 10
                dd, mm, rr =re.findall(r"([0-9]*)[.]([0-9]*)[.]([0-9]*)", zamestnanci[zd.priezvisko][7])[0]
                vymer = PlatovyVymer(
                    cislo_zamestnanca = zamestnanci[zd.priezvisko][0],
                    zamestnanec = osoba,
                    datum_od = date(int(rr),int(mm),int(dd)),
                    #datum_do = zamestnanci[zd.priezvisko][X],
                    tarifny_plat = float(zamestnanci[zd.priezvisko][8].replace(",",".")),
                    osobny_priplatok = float(zamestnanci[zd.priezvisko][9].replace(",",".")),
                    platova_trieda = zamestnanci[zd.priezvisko][4],
                    platovy_stupen = zamestnanci[zd.priezvisko][5],
                    uvazok = float(zamestnanci[zd.priezvisko][6].replace(",",".")),
                    praxroky = osoba.zapocitane_roky,
                    praxdni = osoba.zapocitane_dni,
                    )
                if zamestnanci[zd.priezvisko][10]:
                    vymer.funkcny_priplatok = float(zamestnanci[zd.priezvisko][10].replace(",","."))
                else:
                    vymer.funkcny_priplatok = 0
                vymer.zdroj = Zdroj.objects.filter(id=1)[0]                         #111
                vymer.program = Program.objects.filter(id=1)[0]                     #Ostatné
                vymer.zakazka = TypZakazky.objects.filter(id=2)[0]                  #11010001 spol. zák.
                vymer.ekoklas = EkonomickaKlasifikacia.objects.filter(id=18)[0]     #611 - Tarifný plat, ...
                dp = datum_postupu(vymer.datum_od, date.today(), (vymer.praxroky, vymer.praxdni))
                vymer.datum_postup = dp[1] if dp else None
                vymer.save()
                # ak máme zadaný aj novší výmer
                if zamestnanci[zd.priezvisko][11]:
                    #trieda2 11	stupen2 12	uvazok2 13	platnyod2 14	tarifny2 15	osobny2 16	riadenie2 17
                    dd, mm, rr =re.findall(r"([0-9]*)[.]([0-9]*)[.]([0-9]*)", zamestnanci[zd.priezvisko][14])[0]
                    vymer2 = PlatovyVymer(
                        cislo_zamestnanca = zamestnanci[zd.priezvisko][0],
                        zamestnanec = osoba,
                        datum_od = date(int(rr),int(mm),int(dd)),
                        #datum_do = zamestnanci[zd.priezvisko][X],
                        tarifny_plat = float(zamestnanci[zd.priezvisko][15].replace(",",".")),
                        osobny_priplatok = float(zamestnanci[zd.priezvisko][16].replace(",",".")),
                        platova_trieda = zamestnanci[zd.priezvisko][11],
                        platovy_stupen = zamestnanci[zd.priezvisko][12],
                        uvazok = float(zamestnanci[zd.priezvisko][13].replace(",",".")),
                        praxroky = osoba.zapocitane_roky,
                        praxdni = osoba.zapocitane_dni,
                        )
                    if zamestnanci[zd.priezvisko][17]:
                        vymer2.funkcny_priplatok = float(zamestnanci[zd.priezvisko][17].replace(",","."))
                    else:
                        vymer2.funkcny_priplatok = 0
                    vymer2.zdroj = Zdroj.objects.filter(id=1)[0]                         #111
                    vymer2.program = Program.objects.filter(id=1)[0]                     #Ostatné
                    vymer2.zakazka = TypZakazky.objects.filter(id=2)[0]                  #11010001 spol. zák.
                    vymer2.ekoklas = EkonomickaKlasifikacia.objects.filter(id=18)[0]     #611 - Tarifný plat, ...

                    # aktualizovať predchádzajúci výmer
                    vymer.datum_do = vymer2.datum_od - timedelta(days=1)
                    #def vypocet_prax(date_from, date_to, zapocitane=(0,0)):
                    years, days = vypocet_zamestnanie(vymer.datum_od, vymer.datum_do)
                    vymer.zamestnanieroky = years
                    vymer.zamestnaniedni = days
                    years, days = vypocet_prax(vymer.datum_od, vymer.datum_do, (vymer.praxroky, vymer.praxdni)) 
                    vymer.praxroky = years 
                    vymer.praxdni = days
                    vymer.datum_postup = None
                    vymer.save()

                    vymer2.praxroky = vymer.praxroky
                    vymer2.praxdni = vymer.praxdni
                    dp = datum_postupu(vymer2.datum_od, date.today(), (vymer2.praxroky, vymer2.praxdni))
                    vymer2.datum_postup = dp[1] if dp else None
                    vymer2.save()
                pass
        pass
