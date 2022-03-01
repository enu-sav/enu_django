import csv, re
from django.core.management import BaseCommand, CommandError
from django.utils import timezone
from ipdb import set_trace as trace
from datetime import date, timedelta
from simple_history.utils import update_change_reason
import openpyxl

from uctovnictvo.models import ZamestnanecDohodar, Zamestnanec, Dohodar, DoVP, DoPC, PlatovyVymer
from uctovnictvo.models import Zdroj, Program, TypZakazky, EkonomickaKlasifikacia
from uctovnictvo.rokydni import datum_postupu, vypocet_prax, vypocet_zamestnanie 

class Command(BaseCommand):
    help = 'Načítať údaje o zamestnancoch a dohodaroch'

    def add_arguments(self, parser):
        #'datumy nastupu ENU HPP-porovnanie.xlsx'
        parser.add_argument('--path', type=str, help="xlsx súbor s dátami o zamestnancoch a dohodároch")

    def read_data(self, path):
        wb = openpyxl.load_workbook(path)
        ws = wb.active
        zamest ={}
        for row in range(3,36):
            mn = ws.cell(row=row, column=1).value.split(",")[0]   #11: priezvisko
            data = []
            data.append(ws.cell(row=row, column=2).value)  #B: os. číslo
            data.append(ws.cell(row=row, column=3).value.date())  #C: Dátum nástupu do ENU
            data.append(ws.cell(row=row, column=7).value)  #11: roky
            data.append(ws.cell(row=row, column=8).value)  #11: dni
            num=19
            data.append(ws.cell(row=row, column=num).value) #Trieda
            num +=1
            data.append(ws.cell(row=row, column=num).value) 
            num +=1
            data.append(ws.cell(row=row, column=num).value) 
            num +=1
            if ws.cell(row=row, column=num).value:
                data.append(ws.cell(row=row, column=num).value.date()) #20, Platný od
            else:
                data.append("")
            num +=1
            data.append(ws.cell(row=row, column=num).value)
            num +=1
            data.append(ws.cell(row=row, column=num).value)
            num +=1
            data.append(ws.cell(row=row, column=num).value)
            num +=1

            num=27
            data.append(ws.cell(row=row, column=num).value) #Trieda
            num +=1
            data.append(ws.cell(row=row, column=num).value) 
            num +=1
            data.append(ws.cell(row=row, column=num).value) 
            num +=1
            data.append(ws.cell(row=row, column=num).value.date()) #28, Platný od
            num +=1
            data.append(ws.cell(row=row, column=num).value)
            num +=1
            data.append(ws.cell(row=row, column=num).value)
            num +=1
            data.append(ws.cell(row=row, column=num).value)
            num +=1

            print(mn)
            zamest[mn]=data
        return zamest

    def handle(self, *args, **kwargs):
        path = kwargs['path']
        zamestnanci = self.read_data(path)
        zd_set = ZamestnanecDohodar.objects.filter()

        for zd in zd_set:
            if zd.priezvisko in zamestnanci:
                print(f"z {zd.priezvisko}")
                osoba = Zamestnanec()
            else:
                print(f"d {zd.priezvisko}")
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
                osoba.cislo_zamestnanca = zamestnanci[zd.priezvisko][0] #os. číslo
                osoba.zamestnanie_od = zamestnanci[zd.priezvisko][1] #Dátum nástupu do ENU
                osoba.zapocitane_roky = int(zamestnanci[zd.priezvisko][2]) #roky
                osoba.zapocitane_dni = int(zamestnanci[zd.priezvisko][3]) #dni
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
                vymer = None
                vymer2 = None
                if zamestnanci[zd.priezvisko][8]:
                    vymer = PlatovyVymer(
                        cislo_zamestnanca = zamestnanci[zd.priezvisko][0],
                        zamestnanec = osoba,
                        #datum_do = zamestnanci[zd.priezvisko][X],
                        tarifny_plat = zamestnanci[zd.priezvisko][8],
                        osobny_priplatok = zamestnanci[zd.priezvisko][9],
                        platova_trieda = zamestnanci[zd.priezvisko][4],
                        platovy_stupen = zamestnanci[zd.priezvisko][5],
                        uvazok = zamestnanci[zd.priezvisko][6],
                        datum_od = zamestnanci[zd.priezvisko][7],
                        praxroky = osoba.zapocitane_roky,
                        praxdni = osoba.zapocitane_dni
                        )
                    if zamestnanci[zd.priezvisko][10]:
                        vymer.funkcny_priplatok = zamestnanci[zd.priezvisko][10]
                    else:
                        vymer.funkcny_priplatok = 0
                    vymer.zdroj = Zdroj.objects.filter(id=1)[0]                         #111
                    vymer.program = Program.objects.filter(id=1)[0]                     #Ostatné
                    vymer.zakazka = TypZakazky.objects.filter(id=2)[0]                  #11010001 spol. zák.
                    vymer.ekoklas = EkonomickaKlasifikacia.objects.filter(id=18)[0]     #611 - Tarifný plat, ...
                    dp = datum_postupu(osoba.zamestnanie_od, date.today(), (vymer.praxroky, vymer.praxdni))
                    print("vymer: ",osoba.zamestnanie_od, osoba.zapocitane_roky, osoba.zapocitane_dni,  dp)
                    vymer.datum_postup = dp[1] if dp else None
                    vymer.save()
                # ak máme zadaný aj novší výmer
                if zamestnanci[zd.priezvisko][11]:
                    #trieda2 11	stupen2 12	uvazok2 13	platnyod2 14	tarifny2 15	osobny2 16	riadenie2 17
                    vymer2 = PlatovyVymer(
                        cislo_zamestnanca = zamestnanci[zd.priezvisko][0],
                        zamestnanec = osoba,
                        #datum_do = zamestnanci[zd.priezvisko][X],
                        datum_od = zamestnanci[zd.priezvisko][14],
                        tarifny_plat = zamestnanci[zd.priezvisko][15],
                        osobny_priplatok = zamestnanci[zd.priezvisko][16],
                        platova_trieda = zamestnanci[zd.priezvisko][11],
                        platovy_stupen = zamestnanci[zd.priezvisko][12],
                        uvazok = zamestnanci[zd.priezvisko][13],
                        )
                    if zamestnanci[zd.priezvisko][17]:
                        vymer2.funkcny_priplatok = zamestnanci[zd.priezvisko][17]
                    else:
                        vymer2.funkcny_priplatok = 0
                    vymer2.zdroj = Zdroj.objects.filter(id=1)[0]                         #111
                    vymer2.program = Program.objects.filter(id=1)[0]                     #Ostatné
                    vymer2.zakazka = TypZakazky.objects.filter(id=2)[0]                  #11010001 spol. zák.
                    vymer2.ekoklas = EkonomickaKlasifikacia.objects.filter(id=18)[0]     #611 - Tarifný plat, ...

                    # aktualizovať predchádzajúci výmer
                    if zd.priezvisko == "Maliňáková":
                        trace()
                        pass
                    if vymer:
                        vymer.datum_do = vymer2.datum_od - timedelta(days=1)
                        #def vypocet_prax(date_from, date_to, zapocitane=(0,0)):
                        years, days = vypocet_zamestnanie(osoba.zamestnanie_od, vymer.datum_do)
                        vymer.zamestnanieroky = years
                        vymer.zamestnaniedni = days
                        years, days = vypocet_prax(osoba.zamestnanie_od, vymer.datum_do, (osoba.zapocitane_roky, osoba.zapocitane_dni)) 
                        vymer.praxroky = years 
                        vymer.praxdni = days
                        vymer.datum_postup = None
                        vymer.save()

                        vymer2.praxroky = vymer.praxroky
                        vymer2.praxdni = vymer.praxdni
                        dp = datum_postupu(osoba.zamestnanie_od, date.today(), (osoba.zapocitane_roky, osoba.zapocitane_dni))
                        print("vymer2: ",osoba.zamestnanie_od, osoba.zapocitane_roky, osoba.zapocitane_dni,  dp)
                        vymer2.datum_postup = dp[1] if dp else None
                        vymer2.save()
                    pass
        pass
