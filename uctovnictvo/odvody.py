from openpyxl import load_workbook
from ipdb import set_trace as trace

# vráti tabuľku odvodov pre zadanú kategóriu
#https://www.podnikajte.sk/socialne-a-zdravotne-odvody/odvody-z-dohody-2021
def TabulkaOdvodov(meno_suboru, zam_doh, typ, vynimka=False):
    #Načítať súbor s údajmi o odvodoch
    workbook = load_workbook(filename=meno_suboru)

    # riadky v tabulke a udajmi o poisteni
    udaje = [4,5,6,7,8,10,12]
    udaje = {
        "nemocenske": 4,
        "starobne": 5,
        "invalidne": 6,
        "nezamestnanecke": 7,
        "urazove": 8,
        "rezervny": 10,
        "zdravotne": 12,
    }

    if zam_doh == "zamestnanec":
        pass
    else:   #dohodar
        ws = workbook["Dohodári"]
        if not ws:
            return f"V súbore '{nazov_objektu}' sa nenachádza hárok 'Dohodári'."

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
def DohodarOdvodySpolu(meno_suboru, odmena, typ, vodmena):
    if typ in ["DoBPS", "StarDoch", "InvDoch"] and vodmena > 0:
        odvody_zam = 0
        odvody_prac = 0
        if odmena > vodmena:    #veľké odvody
            tz, tp = TabulkaOdvodov(meno_suboru, "dohodar", typ)
            odvody_zam = sum([(odmena-vodmena) * tz[tt] for tt in tz])
            odvody_prac = sum([(odmena-vodmena) * tp[tt] for tt in tp])
        # malé odvody
        tz, tp = TabulkaOdvodov(meno_suboru, "dohodar", typ, vynimka=True)
        odvody_zam += sum([vodmena * tz[tt] for tt in tz])
        odvody_prac += sum([vodmena * tp[tt] for tt in tp])
    else:
        tz, tp = TabulkaOdvodov(meno_suboru, "dohodar", typ)
        odvody_zam = sum([odmena * tz[tt] for tt in tz])
        odvody_prac = sum([odmena * tp[tt] for tt in tp])
    return round(odvody_zam, 2), round(odvody_prac, 2) 

def main():
    smeno = '/home/milos/Beliana/Django/enu_django-dev/data/Subory/SablonyASubory/OdvodyZamestnanciDohodari.xlsx'
    suma = 100
    vodmena = 200

    print("DoPC 100 (34.95, 13.4) ", DohodarOdvodySpolu(smeno, suma, "DoPC", 0))
    print("DoVP 100 (32.55, 11.0)", DohodarOdvodySpolu(smeno, suma, "DoVP", 0))
    print("DoBPS 100 (22.55, 7.0)", DohodarOdvodySpolu(smeno, suma, "DoBPS", 0))
    print("InvDoch 100 (22.55, 7.0)", DohodarOdvodySpolu(smeno, suma, "StarDoch", 0))
    print("StarDoch 100 (19.55, 4.0)", DohodarOdvodySpolu(smeno, suma, "InvDoch", 0))
    print()

    print("DoPC 100 (34.95, 13.4)", DohodarOdvodySpolu(smeno, suma, "DoPC", 200))
    print("DoVP 100 (32.55, 11.0)", DohodarOdvodySpolu(smeno, suma, "DoVP", 200))
    print("DoBPS 100 (1.6, 0.0)", DohodarOdvodySpolu(smeno, suma, "DoBPS", 200))
    print("StarDoch 100 (1.6, 0.0)", DohodarOdvodySpolu(smeno, suma, "StarDoch", 200))
    print("InvDoch 100 (1.6, 0.0)", DohodarOdvodySpolu(smeno, suma, "InvDoch", 200))
    print()

    print("DoPC 200 (69.9, 26.8)", DohodarOdvodySpolu(smeno, 2*suma, "DoPC", 200))
    print("DoVP 200 (65.1, 22.0)", DohodarOdvodySpolu(smeno, 2*suma, "DoVP", 200))
    print("DoBPS 200 (1.6, 0.0)", DohodarOdvodySpolu(smeno, 2*suma, "DoBPS", 200))
    print("StarDoch 200 (1.6, 0.0)", DohodarOdvodySpolu(smeno, 2*suma, "StarDoch", 200))
    print("InvDoch 200 (1.6, 0.0)", DohodarOdvodySpolu(smeno, 2*suma, "InvDoch", 200))
    print()

    print("DoPC 300 (104.85, 40.2)", DohodarOdvodySpolu(smeno, 3*suma, "DoPC", 200))
    print("DoVP 300 (97.65, 33.0)", DohodarOdvodySpolu(smeno, 3*suma, "DoVP", 200))
    print("DoBPS 300 (24.15, 7.0)", DohodarOdvodySpolu(smeno, 3*suma, "DoBPS", 200))
    print("StarDoch 300 (21.15, 4.0)", DohodarOdvodySpolu(smeno, 3*suma, "StarDoch", 200))
    print("InvDoch 300 (24.15, 7.0)", DohodarOdvodySpolu(smeno, 3*suma, "InvDoch", 200))
    
if __name__ == "__main__":
    main()