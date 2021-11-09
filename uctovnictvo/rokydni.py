# modul na výpočet rokov a dní pre dobu zamestnania, výpočet praxe a veku zamestnanca
from datetime import date, timedelta
from ipdb import set_trace as trace

# vypočítať počet priestupných dní v období 'days' dní pred zadaným dátumom
# použiť na prepočet doby zamestnania na prax
# predpokladá sa, že days < 365 (netestované)
def leapday_corr(date_to, days):
    #correction for the case when date_to is 29.2
    if date_to.month == 2 and date_to.day == 29:
        date_to += timedelta(days=1)
    date_from = date_to - timedelta(days=days)
    from_leap = not date_from.year%4
    to_leap = not date_to.year%4
    #print(date_from, date_to)
    if from_leap and date_from <= date(date_from.year, 2, 29) and date(date_from.year, 2, 29) < date_to:
        return 1
    if to_leap and date_from <= date(date_to.year, 2, 29) and date(date_to.year, 2, 29) < date_to:
        return 1
    return 0

#Vyráta prax (nezaráta 29. 2, ak padne do obdobia zvyšných dní po celých rokoch
#Parametre: 
# date_from: deň nástupu do zamestnania
# date_to: posledný deň zamestnania
# zapocitane: (roky, dni) započítanej praxe z predchádzajúcich zamestnaní
def vypocet_prax(date_from, date_to, zapocitane=(0,0)):
    years, days = vypocet_zamestnanie(date_from, date_to)
    #korekcia na 29. 2
    days -= leapday_corr(date_to, days)
    zr = zapocitane[0]
    zd = zapocitane[1]
    years += zr + int((days+zd)/365)
    days = (days+zd)%365
    return years, days

#Výpočet dĺžky zamestnania
#Parametre: 
# date_from: deň nástupu do zamestnania
# date_to: posledný deň zamestnania
#Vráti (years, days), pričom 'days' zarátava 29.2, ak padne do obdobia zvyšných dní po celých rokoch
def vypocet_zamestnanie(date_from, date_to):
    date_to += timedelta(days=1)

    if date_from == date_to:
        #print(1, date_from, date_to, 0, 0)
        years = 0
        days = 0

    elif date_to.day == date_from.day and date_to.month == date_from.month:
        #print(2,date_from, date_to,  date_to.year - date_from.year, 0)
        years = date_to.year - date_from.year
        days = 0

    else:
        years = date_to.year - date_from.year
        aux = date(date_to.year, date_from.month, date_from.day)
        if date_to >= aux:
            days = (date_to - aux).days
            #print(3,date_from, aux, date_to,  years, days)
        else:
            years -= 1
            aux1 = date(date_to.year-1, date_from.month, date_from.day)
            days = (date_to - aux1).days
            #print(4,date_from, aux1, date_to,  years, days)
    return years, days

#určí vek osoby k určenému dátumu. 
def vypocet_vek(datumnarodenia, datum):
    # odpočítať 1 deň, aby v prípade zadania dňa narodenín vyšiel počet celých rokov
    return vypocet_prax(datumnarodenia, datum+timedelta(days=-1))

# Výpočet nasledujúceho dátumu zvyšovania platového stupňa vzhľadom na zadaný dátum
# Podľa: Zákon č. 553/2003 Z. z.
# Zákon o odmeňovaní niektorých zamestnancov pri výkone práce vo verejnom záujme a o zmene a doplnení niektorých zákonov
# Parametre:
# datum_nastupu: dátum nástupu do zamestnania
# datum: dátum, ku ktorému sa robí výpočet
# zapocitana_prax: prax započítané ku dňu nástupu
# return: (rozhodujúci deň, dátum zvyšovania, nový stupeň)

def datum_postupu(datum_nastupu, datum, zapocitana_prax):
    # Podľa: Zákon č. 553/2003 Z. z.
    roky_postupu = [0, 2, 4, 6, 9, 12, 15, 18, 21, 24, 28, 32, 36, 40]
    # nový stupeň po dosiahnutí rokov postupu
    plat_stupen = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14"]
    
    akt_prax = vypocet_prax(datum_nastupu, datum, zapocitana_prax)
    # nad 40 rokov sa nezvyšuje
    if akt_prax[0] >= 40: return None

    #určiť rozhodujúci deň
    #vypočítať dátum, keď naposledy uplynul celý počet rokov praxe
    #korekcia "-1": lebo vypocet_prax(d,d) = (0,1)
    dd = datum - timedelta(akt_prax[1] + leapday_corr(datum, akt_prax[1]) - 1)

    #určiť, ktorá hodnota roku postupu prichádza do úvahy
    for nn, nval in enumerate(roky_postupu):
        if nval - akt_prax[0] > 0: break

    # rozhodujúci deň
    d_day = date(dd.year+roky_postupu[nn]-akt_prax[0], dd.month, dd.day)

    #trace()
    return d_day, date(d_day.year, d_day.month, 1), plat_stupen[nn]

def main():
    print("postup", datum_postupu(date(2020,1,1), date(2020,1,1), (0,0)) == (date(2022, 1, 1), date(2022, 1, 1), "2"))
    print("postup", datum_postupu(date(2020,1,1), date(2020,1,1), (1,0)) == (date(2021, 1, 1), date(2021, 1, 1), "2"))
    print("postup", datum_postupu(date(2020,1,1), date(2020,1,1), (2,0)) == (date(2022, 1, 1), date(2022, 1, 1), "3"))
    print("postup", datum_postupu(date(2020,1,1), date(2020,1,1), (3,0)) == (date(2021, 1, 1), date(2021, 1, 1), "3"))
    print("postup", datum_postupu(date(2020,1,1), date(2020,1,1), (4,0)) == (date(2022, 1, 1), date(2022, 1, 1), "4"))
    print("postup", datum_postupu(date(2020,1,1), date(2020,1,1), (5,0)) == (date(2021, 1, 1), date(2021, 1, 1), "4"))
    print("postup", datum_postupu(date(2020,1,1), date(2020,1,1), (6,0)) == (date(2023, 1, 1), date(2023, 1, 1), "5"))
    print("postup", datum_postupu(date(2020,1,1), date(2020,1,1), (7,0)) == (date(2022, 1, 1), date(2022, 1, 1), "5"))
    print("postup", datum_postupu(date(2020,1,1), date(2020,1,1), (8,0)) == (date(2021, 1, 1), date(2021, 1, 1), "5"))
    print()
    print("postup", datum_postupu(date(2020,1,15), date(2020,3,1), (0,0)) == (date(2022, 1, 15), date(2022, 1, 1), "2"))
    print("postup", datum_postupu(date(2020,1,15), date(2020,3,1), (1,0)) == (date(2021, 1, 15), date(2021, 1, 1), "2"))
    print("postup", datum_postupu(date(2020,1,15), date(2020,3,1), (2,0)) == (date(2022, 1, 15), date(2022, 1, 1), "3"))
    print("postup", datum_postupu(date(2020,1,15), date(2020,3,1), (3,0)) == (date(2021, 1, 15), date(2021, 1, 1), "3"))
    print("postup", datum_postupu(date(2020,1,15), date(2020,3,1), (4,0)) == (date(2022, 1, 15), date(2022, 1, 1), "4"))
    print("postup", datum_postupu(date(2020,1,15), date(2020,3,1), (5,0)) == (date(2021, 1, 15), date(2021, 1, 1), "4"))
    print("postup", datum_postupu(date(2020,1,15), date(2020,3,1), (6,0)) == (date(2023, 1, 15), date(2023, 1, 1), "5"))
    print("postup", datum_postupu(date(2020,1,15), date(2020,3,1), (7,0)) == (date(2022, 1, 15), date(2022, 1, 1), "5"))
    print("postup", datum_postupu(date(2020,1,15), date(2020,3,1), (8,0)) == (date(2021, 1, 15), date(2021, 1, 1), "5"))
    print()
    print("postup", datum_postupu(date(2010,1,15), date(2020,3,1), (0,0)) == (date(2022, 1, 15), date(2022, 1, 1), "6"))
    print("postup", datum_postupu(date(2010,1,15), date(2020,3,1), (1,0)) == (date(2021, 1, 15), date(2021, 1, 1), "6"))
    print("postup", datum_postupu(date(2010,1,15), date(2020,3,1), (2,0)) == (date(2023, 1, 15), date(2023, 1, 1), "7"))
    print("postup", datum_postupu(date(2010,1,15), date(2020,3,1), (3,0)) == (date(2022, 1, 15), date(2022, 1, 1), "7"))
    print("postup", datum_postupu(date(2010,1,15), date(2020,3,1), (4,0)) == (date(2021, 1, 15), date(2021, 1, 1), "7"))
    print("postup", datum_postupu(date(2010,1,15), date(2020,3,1), (5,0)) == (date(2023, 1, 15), date(2023, 1, 1), "8"))
    print("postup", datum_postupu(date(2010,1,15), date(2020,3,1), (6,0)) == (date(2022, 1, 15), date(2022, 1, 1), "8"))
    print("postup", datum_postupu(date(2010,1,15), date(2020,3,1), (7,0)) == (date(2021, 1, 15), date(2021, 1, 1), "8"))
    print("postup", datum_postupu(date(2010,1,15), date(2020,3,1), (8,0)) == (date(2023, 1, 15), date(2023, 1, 1), "9"))
    print()
    print("postup", datum_postupu(date(2010,8,15), date(2020,3,1), (0,0)) == (date(2022, 8, 15), date(2022, 8, 1), "6"))
    print("postup", datum_postupu(date(2010,8,15), date(2020,3,1), (1,0)) == (date(2021, 8, 15), date(2021, 8, 1), "6"))
    print("postup", datum_postupu(date(2010,8,15), date(2020,3,1), (2,0)) == (date(2020, 8, 15), date(2020, 8, 1), "6"))
    print("postup", datum_postupu(date(2010,8,15), date(2020,3,1), (3,0)) == (date(2022, 8, 15), date(2022, 8, 1), "7"))
    print("postup", datum_postupu(date(2010,8,15), date(2020,3,1), (4,0)) == (date(2021, 8, 15), date(2021, 8, 1), "7"))
    print("postup", datum_postupu(date(2010,8,15), date(2020,3,1), (5,0)) == (date(2020, 8, 15), date(2020, 8, 1), "7"))
    print("postup", datum_postupu(date(2010,8,15), date(2020,3,1), (6,0)) == (date(2022, 8, 15), date(2022, 8, 1), "8"))
    print("postup", datum_postupu(date(2010,8,15), date(2020,3,1), (7,0)) == (date(2021, 8, 15), date(2021, 8, 1), "8"))
    print("postup", datum_postupu(date(2010,8,15), date(2020,3,1), (8,0)) == (date(2020, 8, 15), date(2020, 8, 1), "8"))
    print()
    print("postup", datum_postupu(date(2010,8,15), date(2020,3,1), (0,22)) == (date(2022, 7, 24), date(2022, 7, 1), "6"))
    print("postup", datum_postupu(date(2010,8,15), date(2020,3,1), (1,22)) == (date(2021, 7, 24), date(2021, 7, 1), "6"))
    print("postup", datum_postupu(date(2010,8,15), date(2020,3,1), (2,22)) == (date(2020, 7, 24), date(2020, 7, 1), "6"))
    print("postup", datum_postupu(date(2010,8,15), date(2020,3,1), (3,22)) == (date(2022, 7, 24), date(2022, 7, 1), "7"))
    print("postup", datum_postupu(date(2010,8,15), date(2020,3,1), (4,22)) == (date(2021, 7, 24), date(2021, 7, 1), "7"))
    print("postup", datum_postupu(date(2010,8,15), date(2020,3,1), (5,22)) == (date(2020, 7, 24), date(2020, 7, 1), "7"))
    print("postup", datum_postupu(date(2010,8,15), date(2020,3,1), (6,22)) == (date(2022, 7, 24), date(2022, 7, 1), "8"))
    print("postup", datum_postupu(date(2010,8,15), date(2020,3,1), (7,22)) == (date(2021, 7, 24), date(2021, 7, 1), "8"))
    print("postup", datum_postupu(date(2010,8,15), date(2020,3,1), (8,22)) == (date(2020, 7, 24), date(2020, 7, 1), "8"))
    print()
    print("postup", datum_postupu(date(2010,7,15), date(2020,3,1), (0,22)) == (date(2022, 6, 23), date(2022, 6, 1), "6"))
    print("postup", datum_postupu(date(2010,7,15), date(2020,3,1), (1,22)) == (date(2021, 6, 23), date(2021, 6, 1), "6"))
    print("postup", datum_postupu(date(2010,7,15), date(2020,3,1), (2,22)) == (date(2020, 6, 23), date(2020, 6, 1), "6"))
    print("postup", datum_postupu(date(2010,7,15), date(2020,3,1), (3,22)) == (date(2022, 6, 23), date(2022, 6, 1), "7"))
    print("postup", datum_postupu(date(2010,7,15), date(2020,3,1), (4,22)) == (date(2021, 6, 23), date(2021, 6, 1), "7"))
    print("postup", datum_postupu(date(2010,7,15), date(2020,3,1), (5,22)) == (date(2020, 6, 23), date(2020, 6, 1), "7"))
    print("postup", datum_postupu(date(2010,7,15), date(2020,3,1), (6,22)) == (date(2022, 6, 23), date(2022, 6, 1), "8"))
    print("postup", datum_postupu(date(2010,7,15), date(2020,3,1), (7,22)) == (date(2021, 6, 23), date(2021, 6, 1), "8"))
    print("postup", datum_postupu(date(2010,7,15), date(2020,3,1), (8,22)) == (date(2020, 6, 23), date(2020, 6, 1), "8"))
    print()
    print("postup", datum_postupu(date(2010,7,15), date(2020,3,1), (0,22)) == (date(2022, 6, 23), date(2022, 6, 1), "6"))
    print("postup", datum_postupu(date(2010,7,15), date(2020,4,1), (0,22)) == (date(2022, 6, 23), date(2022, 6, 1), "6"))
    print("postup", datum_postupu(date(2010,7,15), date(2020,5,1), (0,22)) == (date(2022, 6, 23), date(2022, 6, 1), "6"))
    print("postup", datum_postupu(date(2010,7,15), date(2020,6,1), (0,22)) == (date(2022, 6, 23), date(2022, 6, 1), "6"))
    print("postup", datum_postupu(date(2010,7,15), date(2020,7,1), (0,22)) == (date(2022, 6, 23), date(2022, 6, 1), "6"))
    print("postup", datum_postupu(date(2010,7,15), date(2020,8,1), (0,22)) == (date(2022, 6, 23), date(2022, 6, 1), "6"))
    print("postup", datum_postupu(date(2010,7,15), date(2020,9,1), (0,22)) == (date(2022, 6, 23), date(2022, 6, 1), "6"))
    print("postup", datum_postupu(date(2010,7,15), date(2020,10,1), (0,22)) == (date(2022, 6, 23), date(2022, 6, 1), "6"))
    print("postup", datum_postupu(date(2010,7,15), date(2020,12,1), (0,22)) == (date(2022, 6, 23), date(2022, 6, 1), "6"))
    print()
    print("postup", datum_postupu(date(2010,7,15), date(2020,3,1), (0,22)) == (date(2022, 6, 23), date(2022, 6, 1), "6"))
    print("postup", datum_postupu(date(2010,7,15), date(2022,3,1), (2,22)) == (date(2023, 6, 23), date(2023, 6, 1), "7"))
    print("postup", datum_postupu(date(2010,7,15), date(2024,3,1), (4,22)) == (date(2024, 6, 23), date(2024, 6, 1), "8"))
    print("postup", datum_postupu(date(2010,7,15), date(2026,3,1), (6,22)) == (date(2028, 6, 23), date(2028, 6, 1), "10"))
    print("postup", datum_postupu(date(2010,7,15), date(2028,3,1), (8,22)) == (date(2030, 6, 23), date(2030, 6, 1), "11"))
    print("postup", datum_postupu(date(2010,7,15), date(2030,3,1), (10,22)) == (date(2032, 6, 23), date(2032, 6, 1), "12"))
    print("postup", datum_postupu(date(2010,7,15), date(2032,3,1), (12,22)) == (date(2034, 6, 23), date(2034, 6, 1), "13"))
    print("postup", datum_postupu(date(2010,7,15), date(2034,3,1), (14,22)) == (date(2036, 6, 23), date(2036, 6, 1), "14"))
    print("postup", datum_postupu(date(2010,7,15), date(2036,3,1), (16,22)) == None)
    print()
    print("postup", datum_postupu(date(2010,1,15), date(2020,3,1), (0,22)) == (date(2021, 12, 24), date(2021, 12, 1), "6"))
    print("postup", datum_postupu(date(2010,1,15), date(2022,3,1), (2,22)) == (date(2022, 12, 24), date(2022, 12, 1), "7"))
    print("postup", datum_postupu(date(2010,1,15), date(2024,3,1), (4,22)) == (date(2026, 12, 24), date(2026, 12, 1), "9"))
    print("postup", datum_postupu(date(2010,1,15), date(2026,3,1), (6,22)) == (date(2027, 12, 24), date(2027, 12, 1), "10"))
    print("postup", datum_postupu(date(2010,1,15), date(2028,3,1), (8,22)) == (date(2029, 12, 24), date(2029, 12, 1), "11"))
    print("postup", datum_postupu(date(2010,1,15), date(2030,3,1), (10,22)) == (date(2031, 12, 24), date(2031, 12, 1), "12"))
    print("postup", datum_postupu(date(2010,1,15), date(2032,3,1), (12,22)) == (date(2033, 12, 24), date(2033, 12, 1), "13"))
    print("postup", datum_postupu(date(2010,1,15), date(2034,3,1), (14,22)) == (date(2035, 12, 24), date(2035, 12, 1), "14"))
    print("postup", datum_postupu(date(2010,1,15), date(2036,3,1), (16,22)) == None)
    print("postup", datum_postupu(date(1990,1,15), date(2030,1,15), (0,0)) == None)
    #humanet, https://humanet.sk/podpora/platove-postupy-plat-postupy
    print()
    print("postup", datum_postupu(date(2019,8,27), date(2019,9,1), (32,256)) == (date(2022, 12, 14), date(2022, 12, 1), "13"))
    trace()
    #print(leapday_corr(date(2020,2,29), 0))
    #print(leapday_corr(date(2020,2,29), 1))
    #print(leapday_corr(date(2020,2,29), 2))
    #print(leapday_corr(date(2020,3,1), 0))
    #print(leapday_corr(date(2020,3,1), 1))
    #print(leapday_corr(date(2020,3,1), 2))
    #print()

    fd = date(2019,1,1) 
    td = date(2020,3,31)
    print(fd, td)
    print("zam: ", vypocet_zamestnanie(fd, td))
    print("prx :", vypocet_prax(fd, td))
    print()
    
    fd = date(2019,1,1) 
    td = date(2020,1,31)
    print(fd, td)
    print("zam: ", vypocet_zamestnanie(fd, td))
    print("prx :", vypocet_prax(fd, td))
    print()
    
    fd = date(2019,1,1) 
    td = date(2020,2,29)
    print(fd, td)
    print("zam: ", vypocet_zamestnanie(fd, td))
    print("prx :", vypocet_prax(fd, td))
    print()
    
    print("Humanet")
    fd=date(2008,10,31)
    td=date(2020,10,9)
    print(fd, td, (18,0))
    print("zam: ", vypocet_zamestnanie(fd, td))
    print("prx :", vypocet_prax(fd, td,(18,0)))
    print()
    
    fd=date(2008,10,31)
    td=date(2020,12,31)
    print(fd, td, (18,0))
    print("zam: ", vypocet_zamestnanie(fd, td))
    print("prx :", vypocet_prax(fd, td,(18,0)))
    print()
    
    print("Humanet priklad")
    fd=date(2017,5,1)
    td=date(2017,5,15)
    print(fd, td)
    print("zam: ", vypocet_zamestnanie(fd, td))
    print("prx :", vypocet_prax(fd, td,(14,122)))
    print()
    
    fd=date(2017,5,1)
    td=date(2017,12,31)
    print(fd, td)
    print("zam: ", vypocet_zamestnanie(fd, td))
    print("prx :", vypocet_prax(fd, td,(14,122)))
    print()
    
if __name__ == "__main__":
    main()
