from openpyxl import load_workbook
from ipdb import set_trace as trace
from datetime import date
#from models import TypDochodku

# vráti tabuľku odvodov pre zadanú kategóriu
#https://www.podnikajte.sk/socialne-a-zdravotne-odvody/odvody-z-dohody-2021
#do roku 2021 sa neplatilo garancne poistenie
def TabulkaOdvodov(meno_suboru, zam_doh, typ, datum, vynimka=False):
    #Načítať súbor s údajmi o odvodoch
    workbook = load_workbook(filename=meno_suboru)


    if zam_doh == "zamestnanec":
        if datum < date(2022,1,1):
            ws = workbook["Zamestnanci"]
            if not ws:
                return f"V súbore '{nazov_objektu}' sa nenachádza hárok 'Zamestnanci'."
            udaje = {
                "nemocenske": 4,
                "starobne": 5,
                "invalidne": 6,
                "nezamestnanecke": 7,
                "urazove": 8,
                "rezervny": 10,
                "zdravotne": 12,
            }
        elif datum < date(2022,3,1):
            ws = workbook["Zamestnanci"]
            if not ws:
                return f"V súbore '{nazov_objektu}' sa nenachádza hárok 'Zamestnanci'."
            udaje = {
                "nemocenske": 4,
                "starobne": 5,
                "invalidne": 6,
                "nezamestnanecke": 7,
                "urazove": 8,
                "garancne": 9,
                "rezervny": 10,
                "zdravotne": 12,
            }
        else:
            ws = workbook["Zamestnanci 2022"]
            if not ws:
                return f"V súbore '{nazov_objektu}' sa nenachádza hárok 'Zamestnanci'."
            udaje = {
                "nemocenske": 4,
                "starobne": 5,
                "invalidne": 6,
                "nezamestnanecke": 7,
                "urazove": 8,
                "garancne": 9,
                "rezervny": 10,
                "financovanie_podpory": 11,
                "zdravotne": 13,
            }

        #stĺpec v tabulke
        if typ == "Bezny":
            col0 = 2    #B
        elif typ == "InvDoch30":
            col0 = 4    #D
        elif typ == "InvDoch70":
            col0 = 6    #F
        elif typ == "StarDoch":
            col0 = 8    #H
        elif typ == "VyslDoch":
            col0 = 10   #J
        else:
            return f"Zadaný neplatný typ zamestnanca {typ}"
    else:   #dohodar
        ws = workbook["Dohodári"]
        if not ws:
            return f"V súbore '{nazov_objektu}' sa nenachádza hárok 'Dohodári'."
        # riadky v tabulke s udajmi o poisteni podľa obdobia platnosti
        udaje = {
            "nemocenske": 4,
            "starobne": 5,
            "invalidne": 6,
            "nezamestnanecke": 7,
            "urazove": 8,
            "rezervny": 10,
            "zdravotne": 12,
        }
        if datum.year > 2021:
            udaje["garancne"] = 9


        #stĺpec v tabulke
        if typ == "DoPC":   #aka Pravidelný príjem
            col0 = 2    #B
        elif typ == "DoVP": #aka Nepravidelný príjem
            col0 = 4    #D
        elif typ == "DoBPS":
            col0 = 6 if vynimka else 8  #F, H
        elif typ == "StarDoch":
            col0 = 10 if vynimka else 12    #J, L
        elif typ == "InvDoch":
            col0 = 14 if vynimka else 16    #N, O
        else:
            return f"Zadaný neplatný typ dohodára {typ}"

    odvody_zam = {}
    odvody_prac = {}

    for pp in udaje:
        odvody_zam[pp] = ws.cell(row=udaje[pp], column=col0).value / 100 
        odvody_prac[pp] = ws.cell(row=udaje[pp], column=col0+1).value / 100
    return odvody_zam, odvody_prac

# vodmena: vyňatá odmena na základe odvodovej výnimky
def DohodarOdvody(meno_suboru, odmena, typ, datum, vodmena):
    if typ in ["DoBPS", "StarDoch", "InvDoch"] and vodmena > 0:
        if odmena > vodmena:    #veľké odvody, nad sumou vodmena
            tz1, tp1 = TabulkaOdvodov(meno_suboru, "dohodar", typ, datum)
            tz, tp = TabulkaOdvodov(meno_suboru, "dohodar", typ, datum, vynimka=True)
            for item1, item in zip(tz1, tz): 
                tz[item] = round((odmena-vodmena)*tz1[item]+vodmena*tz[item], 2)
            for item1, item in zip(tp1, tp): 
                tp[item] = round((odmena-vodmena)*tp1[item]+vodmena*tp[item], 2)
        # malé odvody
        else:
            tz, tp = TabulkaOdvodov(meno_suboru, "dohodar", typ, datum, vynimka=True)
            for item in tz: tz[item] = round(odmena*tz[item], 2)
            for item in tp: tp[item] = round(odmena*tp[item], 2)
    else:
        tz, tp = TabulkaOdvodov(meno_suboru, "dohodar", typ, datum)
        for item in tz: 
            tz[item] = round(odmena*tz[item], 2)
        for item in tp: 
            tp[item] = round(odmena*tp[item], 2)
    return tz, tp

def DohodarOdvodySpolu(meno_suboru, odmena, typ, datum, vodmena):
    odvody_zam, odvody_prac = DohodarOdvody(meno_suboru, odmena, typ, datum, vodmena)
    return sum(odvody_zam.values()), sum(odvody_prac.values())

def ZamestnanecOdvody(meno_suboru, odmena, typ, datum):
    tz, tp = TabulkaOdvodov(meno_suboru, "zamestnanec", typ, datum)
    for item in tz: tz[item] = round(odmena*tz[item], 2)
    for item in tp: tp[item] = round(odmena*tp[item], 2)
    return tz, tp

def ZamestnanecOdvodySpolu(meno_suboru, odmena, typ, datum):
    odvody_zam, odvody_prac = ZamestnanecOdvody(meno_suboru, odmena, typ, datum)
    return sum(odvody_zam.values()), sum(odvody_prac.values())

smeno = '/home/milos/Beliana/Django/enu_django-dev/data/Subory/SablonyASubory/OdvodyZamestnanciDohodari.xlsx'
def dohodari_test():
    suma = 100
    vodmena = 200
    datum = date(2022,1,1)

    print(f"Testy pre mesiac {datum}")
    print()

    print("DoPC 100 (35.2, 13.4) ", DohodarOdvodySpolu(smeno, suma, "DoPC", datum, 0))
    print("DoVP 100 (32.8, 11.0)", DohodarOdvodySpolu(smeno, suma, "DoVP", datum, 0))
    print("DoBPS 100 (22.8, 7.0)", DohodarOdvodySpolu(smeno, suma, "DoBPS", datum, 0))
    print("StarDoch 100 (19.8, 4.0)", DohodarOdvodySpolu(smeno, suma, "StarDoch", datum, 0))
    print("InvDoch 100 (22.8, 7.0)", DohodarOdvodySpolu(smeno, suma, "InvDoch", datum, 0))
    print()

    print("DoPC 100 (35.2, 13.4)", DohodarOdvodySpolu(smeno, suma, "DoPC", datum, 200))
    print("DoVP 100 (32.8, 11.0)", DohodarOdvodySpolu(smeno, suma, "DoVP", datum, 200))
    print("DoBPS 100 (1.05, 0.0)", DohodarOdvodySpolu(smeno, suma, "DoBPS", datum, 200))
    print("StarDoch 100 (1.05, 0.0)", DohodarOdvodySpolu(smeno, suma, "StarDoch", datum, 200))
    print("InvDoch 100 (1.05, 0.0)", DohodarOdvodySpolu(smeno, suma, "InvDoch", datum, 200))
    print()

    print("DoPC 200 (70.2, 26.8)", DohodarOdvodySpolu(smeno, 2*suma, "DoPC", datum, 200))
    print("DoVP 200 (65.6, 22.0)", DohodarOdvodySpolu(smeno, 2*suma, "DoVP", datum, 200))
    print("DoBPS 200 (2.1, 0.0)", DohodarOdvodySpolu(smeno, 2*suma, "DoBPS", datum, 200))
    print("StarDoch 200 (2.1, 0.0)", DohodarOdvodySpolu(smeno, 2*suma, "StarDoch", datum, 200))
    print("InvDoch 200 (2.1, 0.0)", DohodarOdvodySpolu(smeno, 2*suma, "InvDoch", datum, 200))
    print()

    print("DoPC 300 (105.4, 40.2)", DohodarOdvodySpolu(smeno, 3*suma, "DoPC", datum, 200))
    print("DoVP 300 (98.4, 33.0)", DohodarOdvodySpolu(smeno, 3*suma, "DoVP", datum, 200))
    print("DoBPS 300 (24.9, 7.0)", DohodarOdvodySpolu(smeno, 3*suma, "DoBPS", datum, 200))
    print("StarDoch 300 (21.9, 4.0)", DohodarOdvodySpolu(smeno, 3*suma, "StarDoch", datum, 200))
    print("InvDoch 300 (24.9, 7.0)", DohodarOdvodySpolu(smeno, 3*suma, "InvDoch", datum, 200))

    #Test podľa výpisu p. Madolovej
    odvody_nit, _ = ZamestnanecOdvody(smeno, 851, "StarDoch", date(2021,10,1))
    odvody_rup, _ = ZamestnanecOdvody(smeno, 1148, "Bezny", date(2021,10,1))
    odvody_ruo, _ = DohodarOdvody(smeno, 360, "DoPC", date(2021,10,1, 0))

    spolu={}
    for nit, rup, ruo in zip(odvody_nit, odvody_rup, odvody_ruo):
        spolu[nit] = round(odvody_nit[nit]+odvody_rup[rup]+odvody_ruo[ruo],2)
    print("nit+rup+ruo")
    print (spolu)
    for nit, rup, ruo in zip(odvody_nit, odvody_rup, odvody_ruo):
        spolu[nit] = round(odvody_nit[nit]+odvody_rup[rup],2)
    print("nit+rup")
    print (spolu)

    print("nit (851)")
    print(odvody_nit)
    print("rup 1148)")
    print(odvody_rup)
    print("ruo (360)")
    print(odvody_ruo)

def zamestnanci_test():
    typy = ["Bezny", "InvDoch30", "InvDoch70", "StarDoch", "VyslDoch"]
    for typ in typy:
        odvody_zam, odvody_prac = ZamestnanecOdvodySpolu(smeno, 100, typ, date(2021,10,1))
        print("%12s %s %2.2f %2.2f"%(typ, date(2021,10,1), odvody_zam, odvody_prac))
    print()

    for typ in typy:
        odvody_zam, odvody_prac = ZamestnanecOdvodySpolu(smeno, 100, typ, date(2022,2,1))
        print("%12s %s %2.2f %2.2f"%(typ, date(2022,2,1), odvody_zam, odvody_prac))
    print()

    for typ in typy:
        odvody_zam, odvody_prac = ZamestnanecOdvodySpolu(smeno, 100, typ, date(2022,8,1))
        print("%12s %s %2.2f %2.2f"%(typ, date(2022,8,1), odvody_zam, odvody_prac))


    
if __name__ == "__main__":
    #dohodari_test()
    zamestnanci_test()
