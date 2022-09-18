# modul na výpočet rokov a dní pre dobu zamestnania, výpočet praxe a veku zamestnanca
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from ipdb import set_trace as trace
import holidays
import re
import numpy as np

mesiace = ["január", "február", "marec", "apríl", "máj", "jún", "júl", "august", "september", "október", "november", "december"]
roky_postupu = [0, 2, 4, 6, 9, 12, 15, 18, 21, 24, 28, 32, 36, 40]
plat_stupen =  [1, 2, 3, 4, 5,  6,  7,  8,  9, 10, 11, 12, 13, 14]

# konvertuje datum v tvare dd.mm.yyyy na date. Namiesto "." môže byť hocijaký znak
def s2d(sdate):
    if not sdate: return sdate
    if type(sdate) == date: return sdate
    dd,mm,yy=re.findall(r"([0-9]+)",sdate)
    return date.fromisoformat('%s-%02d-%02d'%(yy,int(mm),int(dd)))

# konvertuje datum v tvare dd.mm.yyyy na date. Namiesto "." môže byť hocijaký znak
def d2s(ddate):
    if type(ddate) == str: return ddate
    return ddate.strftime("%-d.%-m.%Y")

#určí vek osoby k určenému dátumu. 
def vypocet_vek(datumnarodenia, datum):
    # odpočítať 1 deň, aby v prípade zadania dňa narodenín vyšiel počet celých rokov
    return vypocet_prax(datumnarodenia, datum+timedelta(days=-1))

#vypočíta dátum platového postupu k 'datum'
def datum_postupu(datum1zam, datum):
    return DvaDatumy(datum1zam, datum).postup

#vypočíta počet rokov platového postupu k 'datum'
def postup_roky(datum1zam, datum):
    return DvaDatumy(datum1zam, datum).rpostup

#vypočíta prax k datum (vratane)
def vypocet_prax(datum1zam, datum):
    return DvaDatumy(datum1zam, datum).roky_dni(vratane=True)

#vypočíta prax k datum (vratane?)
def vypocet_zamestnanie(datumenu, datum):
    return DvaDatumy(datumenu, datum).roky_dni(vratane=True)

# Výpočet nasledujúceho dátumu zvyšovania platového stupňa vzhľadom na zadaný dátum
# Podľa: Zákon č. 553/2003 Z. z.
# Zákon o odmeňovaní niektorých zamestnancov pri výkone práce vo verejnom záujme a o zmene a doplnení niektorých zákonov
# Parametre:
# datum_nastupu: virtuálny dátum nástupu do zamestnania (vypočítaný z dátumu nástupu a priznanej praxe)
# datum: dátum, ku ktorému sa robí výpočet
# zapocitana_prax: prax započítané ku dňu nástupu
# return: (rozhodujúci deň, dátum zvyšovania, nový stupeň)

class DvaDatumy():
    def __init__(self, prvy=None, druhy=None, prax=None):
        prvy = s2d(prvy)
        druhy = s2d(druhy)
        if prvy and druhy:
            self.prvy = prvy
            self.druhy = druhy
        elif prvy and prax: #vypočíta 'druhy' tak, že priráta 'prax' k 'prvý'
            self.prvy = prvy
            self.druhy = date(self.prvy.year+prax[0], self.prvy.month,self.prvy.day) + timedelta(days=prax[1])
        elif druhy and prax:    #vypočíta 'prvý' tak, že odráta 'prax' od 'druhý'
            self.druhy = druhy
            #najskôr odpočítať dni od druhy, aby sa zobralo do úvahy, či ide o priestupný rok
            aux = druhy - timedelta(days=prax[1])
            # potom odčítať roky
            self.prvy = date(aux.year - prax[0], aux.month, aux.day) 
        self.datum_postupu()

    # Vypočíta údaje platového postupu k 'druhy'.
    # Ak 'druhy' je dátum postupu, určí 'druhy' ako dátum postupu
    def datum_postupu(self):
        # Podľa: Zákon č. 553/2003 Z. z.
        # Vysvetlenie: do 32 rokov praxe platí stupeň 12, teda pri dosiahnutí 32 praxe sa zvyšuje na 13
        # nový stupeň po dosiahnutí rokov postupu

        # určiť všetky rozhodujúce dni platového postupu
        rn = self.prvy.year
        mn = self.prvy.month
        dn = self.prvy.day
        rozhodujuce_dni = [date(rn+rp, mn, dn) for rp in roky_postupu] 
        # určiť rozhodujúci deň
        for nn, rd in enumerate(rozhodujuce_dni):
            if rd >= self.druhy: break
        #rozhodujúci deň postupu
        self.dpostup = rd
        #deň postupu
        self.postup = date(rd.year, rd.month, 1)
        #nový stupeň
        self.spostup = plat_stupen[nn]
        #odpracované roky ku dňu postupu
        self.rpostup = roky_postupu[nn]

    #Výpočet počtu rokov a dní medzi dvomi dátumami
    #vratane:
    # False: nezaráta posledný deň do počtu, čiže od 1.1.2020 do 1.1.2021 vráti (1,0)
    # Používať: 
    #   ak prvy je 1. deň zamestnania a druhy je 1. deň zamestnania v EnÚ
    #   ak prvy je 1. deň doby a druhy je posledný deň doby
    # True: nezaráta posledný deň do počtu, čiže od 1.1.2020 do 1.1.2021 vráti (1,1)
    #Vráti (years, days), pričom 'days' zarátava 29.2, ak padne do obdobia zvyšných dní po celých rokoch
    def roky_dni(self, vratane=True):
        #Ak 15.1 začne a 15.1 aj skončí, tak pracoval 1 deň
        if self.prvy == self.druhy:
            #print(1, self.prvy, self.druhy, 0, 0)
            years = 0
            days = 1 if vratane else 0

        elif self.druhy.day == self.prvy.day and self.druhy.month == self.prvy.month:
            #print(2,self.prvy, self.druhy,  self.druhy.year - self.prvy.year, 0)
            years = self.druhy.year - self.prvy.year
            days = 1 if vratane else 0
 
        else:
            if vratane:
                self.druhy += timedelta(days=1)
            years = self.druhy.year - self.prvy.year
            aux = date(self.druhy.year, self.prvy.month, self.prvy.day)
            if self.druhy >= aux:
                days = (self.druhy - aux).days 
                #print(3,self.prvy, aux, self.druhy,  years, days)
            else:
                years -= 1
                aux1 = date(self.druhy.year-1, self.prvy.month, self.prvy.day)
                days = (self.druhy - aux1).days
                #print(4,self.prvy, aux1, self.druhy,  years, days)
        return years, days

#vypočítať počet pracovných dní
#sviatky sa ignorujú
#od, do: očakávame, že sú len v jednom mesiaci
#do: vrátane
#do: aj nie je zadané, rátame za celý mesiac
def prac_dni(od, do = None):
    #Vygenerovať sviatky za aktuálny rok
    _sviatky = holidays.SK()
    _ = od in _sviatky #vlastné generovanie za aktuálny rok
    sviatky = [sv.isoformat() for sv in _sviatky.keys()]
    #print(sviatky)
    #Pracovné dni v mesiaci
    if do:
        #print(od,do)
        return np.busday_count(od, do + timedelta(days=1))
        #return np.busday_count(od, do + timedelta(days=1), holidays=sviatky)
    else:
        m1 = date(od.year,od.month,1)
        mp = date(od.year+1 if od.month==12 else od.year, 1 if od.month==12 else od.month+1, 1)
        return np.busday_count(m1, mp)
        #return np.busday_count(m1, mp, holidays=sviatky)

#vypočítať počet pracovných dní
#sviatky sa ignorujú
#od, do: očakávame, že sú len v jednom mesiaci. Použité na výpočet neprítomnosti, sviatky sú brané, akoby bol zamestnanec v práci
#do: vrátane
#do: aj nie je zadané, rátame za celý mesiac. Sviatky sú ignorované
#ppd: počet prac. dní v týždni. 
def prac_dni(od, do = None, ppd=None, zahrnut_sviatky=False):
    #Pracovné dni v mesiaci
    if not ppd:
        wm=[1,1,1,1,1,0,0]
    elif ppd == 1:
        wm=[0,0,1,0,0,0,0]  #Predpokladáme, že pracuje v stredu
    elif ppd == 2:
        wm=[0,1,1,0,0,0,0]  #Predpokladáme, že pracuje Utorok - Stredu
    elif ppd == 3:
        wm=[0,1,1,1,0,0,0]  #Predpokladáme, že pracuje Utorok - Štvrtok
    elif ppd == 4:
        wm=[1,1,1,1,1,0,0]  #Predpokladáme, že pracuje Pondelok - Štvrtok
    elif ppd == 5:
        wm=[1,1,1,1,1,0,0]  #Predpokladáme, že pracuje Pondelok - Piatok
    if do:
        #print(od,do)
        #Vygenerovať sviatky za aktuálny rok
        _sviatky = holidays.SK()
        _ = od in _sviatky #vlastné generovanie za aktuálny rok
        sviatky = [sv.isoformat() for sv in _sviatky.keys()]
        return np.busday_count(od, do + timedelta(days=1), weekmask=wm, holidays=[] if zahrnut_sviatky else sviatky)
    else:   #Sviatky sa zahrnú vždy bez ohľadu na parameter zahrnut_sviatky
        m1 = date(od.year,od.month,1)
        mp = date(od.year+1 if od.month==12 else od.year, 1 if od.month==12 else od.month+1, 1)
        return np.busday_count(m1, mp, weekmask=wm)

def prekryv_dni(mesiac, od, do):
    from collections import namedtuple
    Range = namedtuple('Range', ['start', 'end'])
    m1 = date(mesiac.year,mesiac.month,1)
    mp = date(mesiac.year+1 if mesiac.month==12 else mesiac.year, 1 if mesiac.month==12 else mesiac.month+1, 1) - timedelta(days=1)
    r1 = Range(start=m1, end=mp)
    r2 = Range(start=od, end=do)
    latest_start = max(r1.start, r2.start)
    earliest_end = min(r1.end, r2.end)
    delta = (earliest_end - latest_start).days + 1
    overlap = max(0, delta)
    return overlap
    

#Výpočet koeficientu neodpracovaných dní pri neúplne odpracovanom mesiaci
#vzorec: koef = počet neodpracovaných dní / počet pracovných dní v mesiaci
#sviatky sa ignoruju
#Koeficient je pre daný mesiac aditívny, možno opakovane odčítať od 1
def koef_neodprac_dni(od, do):
    '''
    od: začiatok neprítomnosti
    do: koniec neprítomnosti (vrátane)
    od, do: očakávame, že sú len v jednom mesiaci
    '''
    return prac_dni(od, do)/prac_dni(od)

def main():
    fr,to,yy,dd=range(4)
    test = [
        ["1.1.2020", "1.3.2020", 0, 60],
        ["1.2.2020", "1.3.2020", 0, 29],
        ["1.1.2019", "1.3.2020", 1, 60],
        ["1.2.2019", "1.3.2020", 1, 29],
        ["1.1.2020", "1.1.2020", 0, 0],
        ["1.1.2020", "2.1.2020", 0, 1],
        ["1.1.2020", "1.1.2021", 1, 0],
        ["1.1.2020", "31.12.2021", 1, 364],
        ["1.1.2020", "1.1.2022", 2, 0],
        ["1.1.2020", "3.1.2022", 2, 2],
        #["1.1.2020", "29.2.2020", 0, 59],
        ["1.1.2019", "1.3.2020", 1, 60],
        [],
        ["1.2.2018", "1.2.2018", 0, 0],
        ["1.2.2018", "2.2.2018", 0, 1],
        ["1.2.2018", "1.1.2020", 1, 334],
        ["1.2.2018", "31.1.2020", 1, 364],
        ["1.2.2018", "1.2.2020", 2, 0],
        ["1.2.2018", "28.2.2020", 2, 27],
        #["1.2.2018", "29.2.2020", 2, 28],
        ["1.2.2018", "1.3.2020", 2, 29],
        [],
        ["18.12.2007", "1.7.2019", 11, 195], #softip: prvý dátum získaný z druhého odčítaním dňov a rokov praxe
        ["1.7.1989", "15.12.1997", 8, 167],
        ["2.5.1992", "1.5.1995", 2, 364],
        ["1.12.2001", "1.12.2001", 0, 0],
        ["1.9.2000", "1.9.2000", 0, 0],
        ["1.7.2006", "1.1.2007", 0, 184],
        ["1.5.1988", "1.5.2010", 22, 0],
        ["28.1.2010", "1.3.2021", 11, 33], #softip: pri výpočte "1.3.2021 - (11,33) najskôr odrátajú roky a potom dni, vyzerá to ako chyba
        ["1.3.1986", "1.3.1998", 12, 0],
        ["1.5.1985", "15.5.1995", 10, 14],
        ["1.11.1987", "1.1.1996", 8, 61],
        ["1.10.2004", "1.10.2004", 0, 0],
        ["7.12.1993", "1.2.2022", 28, 56],
        ["1.8.1988", "1.11.2002", 14, 92],
        ["1.1.1973", "3.4.2009", 36, 92],
        ["1.10.2015", "1.2.2018", 2, 123],
        ["1.11.1990", "20.5.1996", 5, 201],
        ["1.10.2012", "1.9.2015", 2, 335],
        ["1.1.1979", "1.8.2014", 35, 212],
        ["1.6.2005", "13.11.2017", 12, 165],
        ["1.5.2005", "1.5.2005", 0, 0],
        ["6.3.2019", "7.9.2020", 1, 185],
        ["1.2.1991", "1.9.1995", 4, 212],
        ["5.10.1982", "1.3.2021", 38, 147],
        ["1.7.1983", "1.9.1994", 11, 62],
        ["1.3.2018", "1.9.2019", 1, 184],
        ["1.5.1986", "2.9.2008", 22, 124],
        ["1.9.2011", "1.8.2017", 5, 334],
        ["1.9.2012", "1.3.2018", 5, 181],
        ["2.12.2006", "1.6.2016", 9, 182]]
    for tt in test:
        #print(tt[0],tt[1], roky_dni(tt[0],tt[1]), tt[2], tt[3])
        pass
    print()
    fmt = "%12s%14s%8s%14s%14s%8s%8s%12s%13s%7s%7s%7s%7s" 
    val = ("Prvý PP(0)", "Nástup EnÚ(1)", "Prax(2)", 
        "0+2->1",
        "1+2->0",
        "0+1->2",
        "test",
        "Rozh. deň",
        "Deň postupu",
        "PlSt.",
        "Roky",
        "PTest1",
        "PTest2"
        )
    print(fmt%val)
    for tt in test:
        if not tt:
            print()
            continue

        d021 = DvaDatumy(prvy=tt[0], prax=(tt[2], tt[3]))
        t021 = s2d(tt[1]) == d021.druhy

        d120 = DvaDatumy(druhy=tt[1], prax=(tt[2], tt[3]))
        t120 = s2d(tt[0]) == d120.prvy

        d012 = DvaDatumy(tt[0], tt[1])
        d012rd = d012.roky_dni(False)
        t012 = tt[2] == d012rd[0] and tt[3] == d012rd[1] 

        #prax k dátumu postupu
        dpost_rd = DvaDatumy(d021.prvy, d021.dpostup).roky_dni(False)

        val = (tt[0],tt[1],f"{tt[2]}.{tt[3]}",
                d2s(d021.druhy),
                d2s(d120.prvy),
                f"{d012rd[0]}.{d012rd[1]}",
                int(t021 and t012 and t120),
                d2s(d021.dpostup),
                d2s(d021.postup),
                d021.spostup,
                d021.rpostup,
                d021.dpostup == d120.dpostup and d021.dpostup == d012.dpostup,
                #f"{dpost_rd[0]}.{dpost_rd[1]}",
                d021.dpostup >= d021.druhy  #Rozhodujúci dátum postupu dpostup k tt[1] nesmie byť menší ako tt[1] ('druhy')
              )
        print(fmt%val)

    print()
    print("Pracovné dni")
    months = [date(2022,1,1), date(2022,2,1), date(2022,3,1), date(2022,4,1), date(2022,5,1), date(2022,6,1), date(2022,7,1), date(2022,8,1), date(2022,9,1), date(2022,10,1), date(2022,11,1)]
    #months = [date(2022,4,1), date(2022,5,1), date(2022,6,1), date(2022,7,1), date(2022,8,1), date(2022,9,1), date(2022,10,1), date(2022,11,1)]
    zac=7
    kon=7
    for tdate in months:
        print(tdate, "za mesiac", prac_dni(tdate))
        print(tdate, "PN    %d %d"%(zac,kon), prac_dni(tdate+timedelta(days=zac), date(tdate.year, tdate.month+1, 1) - timedelta(days=1+kon)))
        #print(tdate, "PN    %d %d"%(zac,0), prac_dni(tdate+timedelta(days=zac), date(tdate.year, tdate.month+1, 1) - timedelta(days=1)))
        #print(tdate, "PN    %d %d"%(0,kon), prac_dni(tdate, date(tdate.year, tdate.month+1, 1) - timedelta(days=1+kon)))
        print(tdate, "Koef  %d %d"%(zac,kon), koef_neodprac_dni(tdate+timedelta(days=zac), date(tdate.year, tdate.month+1, 1) - timedelta(days=1+kon)))
        print()

    print("Prekryv dní")
    print(0, prekryv_dni(date(2022,4,5), date(2022,3,25),date(2022,3,27)))  #xxXX
    print(0, prekryv_dni(date(2022,4,5), date(2022,3,25),date(2022,3,31)))  #xxXX
    print(1, prekryv_dni(date(2022,4,5), date(2022,3,25),date(2022,4,1)))   #xxXX
    print(2, prekryv_dni(date(2022,4,5), date(2022,3,25),date(2022,4,2)))
    print(1, prekryv_dni(date(2022,4,5), date(2022,4,2), date(2022,4,2)))
    print(3, prekryv_dni(date(2022,4,5), date(2022,4,2), date(2022,4,4)))
    print(3, prekryv_dni(date(2022,4,5), date(2022,4,2), date(2022,4,2)+timedelta(days=2)))
    print(7, prekryv_dni(date(2022,4,5), date(2022,4,2)+timedelta(days=3), date(2022,4,9)+timedelta(days=2)))
    print(3, prekryv_dni(date(2022,4,5), date(2022,4,28), date(2022,4,30)))
    print(3, prekryv_dni(date(2022,4,5), date(2022,4,28), date(2022,5,1)))
    print(3, prekryv_dni(date(2022,4,5), date(2022,4,28), date(2022,5,5)))
    print(30, prekryv_dni(date(2022,4,5), date(2022,3,28), date(2022,5,5)))

if __name__ == "__main__":
    main()
