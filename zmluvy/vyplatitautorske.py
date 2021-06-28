
import os, csv, re
from glob import glob
from datetime import date
from django.conf import settings
from django.contrib import messages
from zmluvy.models import OsobaAutor, ZmluvaAutor, PlatbaAutorskaOdmena, PlatbaAutorskaSumar
from openpyxl import load_workbook
from openpyxl.styles import Font, Color, colors, Alignment, PatternFill , numbers
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.pagebreak import Break
from ipdb import set_trace as trace


class VyplatitAutorskeOdmeny():
    ws_template = f"{settings.TEMPLATES_DIR}/UhradaAutHonoraru.xlsx"
    ah_cesta = settings.ROYALTIES_DIR
    litfond_odvod = 0   #Aktuálne 0 kvôli Covid pandémii, inak 2 %
    dan_odvod = 19    # daň, napr. 19 %
    min_vyplatit=20     #minimálna suma v Eur, ktorá sa vypláca
    ucetEnÚ = "SK36 8180 0000 0070 0061 8734 - Beliana"
    ucetLitFond  = "SK47 0200 0000 0012 2545 9853" 
    ucetFin = "SK61 8180 5002 6780 2710 3305"
    WARNING, ERROR, SUCCESS = (1,2,3)

    #def __init__(self, za_mesiac, datum_vyplatenia=None):
        #self.vyplatit_odmeny(za_mesiac, datum_vyplatenia)
    def __init__(self, subory_dir):
        self.ah_cesta = subory_dir
        self.logs = []
        pass
        #self.vyplatit_odmeny(za_mesiac, datum_vyplatenia)

    def log(self, status, msg):
        self.logs.append([status,msg])

    def get_logs(self):
        return self.logs

    def nacitat_udaje_grafik(self, fname):
        pass

    def hlavicka_test(self, fname, row):
        # povinné stĺpce v csv súbore:
        povinne = ["Nid", "Prihlásiť sa", "Zmluva na vyplatenie", "Vyplatenie odmeny", "Dĺžka autorom odovzdaného textu", "Dátum záznamu dĺžky", "Dátum vyplatenia"]
        for item in povinne:
            if not item in row:
                raise Exception(f"Súbor {fname} musí obsahovať stĺpec '{item}'")

    def nacitat_udaje_autor(self, fname, rs_webrs):
        hdr = {}
        with open(fname, 'rt') as f:
            reader = csv.reader(f, dialect='excel')
            hdrOK = False
            for row in reader:
                if not hdrOK:
                    self.hlavicka_test(fname, row)
                    for n, ii in enumerate(row):
                        hdr[ii]=n
                    hdrOK = True
                if row[hdr["Vyplatenie odmeny"]] == "Heslo vypracoval autor, vyplatiť" and not row[hdr["Dátum vyplatenia"]]:
                    login = row[hdr["Prihlásiť sa"]]
                    zmluva = row[hdr['Zmluva na vyplatenie']].strip()   # odstranit medzery na zaciatku a konci
                    if not zmluva:
                        self.log(messages.ERROR, f"Heslo {row[hdr['nazov']]} autora {row[hdr['Prihlásiť sa']]} nemá určenú zmluvu")
                    #if not login in self.pocet_znakov: self.pocet_znakov[login] = {}
                    #if not zmluva in self.pocet_znakov[login]: self.pocet_znakov[login][zmluva] = {}
                    #self.pocet_znakov[login][zmluva] += int(row[hdr["Dĺžka autorom odovzdaného textu"]])
                    # zaznamenat len udaje o hesle a zmluve
                    if not login in self.data: self.data[login] = {} 
                    if not rs_webrs in self.data[login]: self.data[login][rs_webrs] = {} 
                    if not zmluva in self.data[login][rs_webrs]: self.data[login][rs_webrs][zmluva] = []
                    nid = row[hdr["Nid"]] if rs_webrs == "rs" else row[hdr["Nid"]].replace("//rs","//webrs")
                    self.data[login][rs_webrs][zmluva].append([
                        int(row[hdr["Dĺžka autorom odovzdaného textu"]]),
                        rs_webrs,
                        f'=HYPERLINK("{nid}";"{row[hdr["nazov"]]}")',
                        row[hdr['Zmluva na vyplatenie']],
                        re.sub(r"<[^>]*>","",row[hdr['Dátum záznamu dĺžky']])
                        ])
                    pass

    def meno_priezvisko(self, autor):
        if autor.titul_pred_menom:
            mp = f"{autor.titul_pred_menom} {autor.meno} {autor.priezvisko}"
        else:
            mp = f"{autor.meno} {autor.priezvisko}"
        if autor.titul_za_menom:
            mp = f"{mp}, {autor.titul_za_menom}"
        return mp.strip()
            
    def vyplatit_odmeny(self, za_mesiac, datum_vyplatenia=None): 
        self.datum_vyplatenia = datum_vyplatenia # Ak None, nevygenerujú sa hárky ImportRS/WEBRS

        self.obdobie = za_mesiac.strip("/").split("/")[-1]

        za_mesiac = os.path.join(self.ah_cesta, za_mesiac) 

        #nájsť csv súbory 
        if not os.path.isdir(za_mesiac):
            raise Exception(f"Priečinok {za_mesiac} nebol nájdený")
        csv_subory = glob(f"{za_mesiac}/*.csv")
        self.pocet_znakov = {"rs": {}, "webrs":{}}
        self.data={}

        for csv_subor in csv_subory:
            if "export_vyplatit_rs" in csv_subor:
                self.log(messages.INFO, f"Načítané údaje zo súboru {csv_subor}")
                hdr = self.nacitat_udaje_autor(csv_subor, "rs")
            elif "export_vyplatit_webrs" in csv_subor:
                self.log(messages.INFO, f"Načítané údaje zo súboru {csv_subor}")
                hdr = self.nacitat_udaje_autor(csv_subor, "webrs")
            elif "_grafik" in csv_subor:
                self.log(messages.INFO, f"Načítané údaje zo súboru {csv_subor}")
                self.nacitat_udaje_grafik(csv_subor)
                pass
            #else:
                #aux_name = csv_subor.split("/")[-1]
                self.log(messages.ERROR, f"V priečinku {self.ah_cesta}/{za_mesiac} bol nájdený neznámy súbor {aux_name}. Súbor odstráňte alebo opravte jeho názov")

        #scitat pocty znakov a rozhodnut, ci sa bude vyplacat
        self.suma_vyplatit={}    # Vyplati sa
        self.suma_preplatok={}   # strhne sa z preplatku
        for autor in self.data:
            # spanning relationship: zmluvna_strana->rs_login
            zdata = ZmluvaAutor.objects.filter(zmluvna_strana__rs_login=autor)
            adata = OsobaAutor.objects.filter(rs_login=autor)
            if not adata:
                self.log(messages.ERROR, f"Autor {autor}: nemá záznam v databáze ")
            adata=adata[0]
            # pomocna struktura na vyplacanie
            zvyplatit = {}
            for zmluva in zdata:
                zvyplatit[zmluva.cislo_zmluvy] = zmluva.honorar_ah
                if zmluva.honorar_ah < 1:
                    self.log(messages.ERROR, f"Zmluva {zmluva.cislo_zmluvy} autora {autor} nemá určený honorár/AH")
                if not zmluva.datum_zverejnenia_CRZ:
                    self.log(messages.ERROR, f"Zmluva {zmluva.cislo_zmluvy} autora {autor} nie je zverejnená v CRZ")
            # vypocitat odmenu za vsetky hesla
            ahonorar = 0 #sucet odmien za jednotlive hesla na zaklade zmluv
            zmluvy_autora = set()
            for rs in self.data[autor]: # rs alebo webrs
                for zmluva in self.data[autor][rs]:
                    zmluvy_autora.add(zmluva)
                    #if not zmluva in zvyplatit:
                    #zmluva = re.sub(r"([^/]*)/(.*)",r"\2-\1",zmluva)
                    if not zmluva in zvyplatit:
                        self.log(messages.ERROR, f"Autor {autor}: nemá v databáze zmluvu {zmluva}")
                    # spocitat zaokruhlene sumy, aby vypocet bol konzistentny so scitanim v harku po_autoroch 
                    ahonorar = ahonorar + sum([round(z[0]*zvyplatit[zmluva]/36000,2) for z in self.data[autor][rs][zmluva]])    #[0]: pocet znakov
                    pass
            ahonorar = round(round(ahonorar,3),2)
            list_of_strings = [str(s) for s in zmluvy_autora]
            zmluvy_autora = ",".join(list_of_strings)
            if ahonorar - adata.preplatok > VyplatitAutorskeOdmeny.min_vyplatit: # bude sa vyplácať, preplatok sa zohľadní a jeho hodnota sa aktualizuje v db
                if adata.preplatok > 0:
                    self.log(messages.INFO, f"Autor %s: bude vyplatené %.2f € (platba %.2f mínus preplatok %.2f)"%(autor,ahonorar - adata.preplatok,ahonorar,adata.preplatok))
                else:
                    self.log(messages.INFO, f"Autor %s: bude vyplatené %.2f €"%(autor, ahonorar))
                self.suma_vyplatit[autor] = [round(ahonorar,2), adata.preplatok, zmluvy_autora]
                #aktualizovať preplatok
                pass
            elif ahonorar < adata.preplatok: # celú sumu možno odpočítať z preplatku
                self.log(messages.INFO, f"Autor %s: Suma %.2f € sa nevyplatí, odpočíta sa od preplatku %.2f €"%(autor, ahonorar,adata.preplatok) )
                self.suma_preplatok[autor] = [ahonorar, adata.preplatok, zmluvy_autora]
                #aktualizovať preplatok
                pass
            else: #po odpočítaní preplatku zostane suma menšia ako VyplatitAutorskeOdmeny.min_vyplatit. Nevyplatí sa, počká sa na ďalšie platby
                if adata.preplatok > 0:
                    self.log(messages.INFO, f"Autor %s: nebude vyplatené %.2f € (nízka suma, platba %.2f mínus preplatok %.2f)"%(autor,ahonorar - adata.preplatok,ahonorar,adata.preplatok))
                else:
                    self.log(messages.INFO, f"Autor %s: nebude vyplatené %.2f € (nízka suma)"%(autor,ahonorar - adata.preplatok) )
                pass
        # styly buniek, https://openpyxl.readthedocs.io/en/default/styles.html
        # default font dokumentu je Arial
        self.fbold = Font(name="Arial", bold=True)
        self.aright = Alignment(horizontal='right')
        acenter = Alignment(horizontal='center')
        aleft = Alignment(horizontal='left')

        workbook = load_workbook(filename=VyplatitAutorskeOdmeny.ws_template)
        vyplatit = workbook[workbook.sheetnames[0]]
        self.vypocet = workbook[workbook.sheetnames[1]]
        self.krycilist = workbook[workbook.sheetnames[2]]
        self.poautoroch = workbook[workbook.sheetnames[3]]

        self.ppos = 1   #poloha počiatočnej bunky v hárku poautoroch, inkrementovaná po každom zázname
        if self.datum_vyplatenia:
            self.importrs = workbook.create_sheet("Import RS")
            self.importrs.column_dimensions["A"].width = 30
            self.importrs["A1"] = "Odkaz"
            self.importrs["B1"] = "Nid"
            self.importrs["C1"] = "datum_vyplatenia"
            self.rpos = 2   #poloha počiatočnej bunky v hárku importrs, inkrementovaná po každom zázname
            self.importwebrs = workbook.create_sheet("Import WEBRS")
            self.importwebrs.column_dimensions["A"].width = 30
            self.importwebrs["A1"] = "Odkaz"
            self.importwebrs["B1"] = "Nid"
            self.importwebrs["C1"] = "datum_vyplatenia"
            self.wpos = 2   #poloha počiatočnej bunky v hárku importwebrs, inkrementovaná po každom zázname

        #krycí list, zapísať základné údaje
        dtoday = date.today().strftime("%d.%m.%Y")
        self.krycilist["A2"].value = self.krycilist["A2"].value.replace("xx-xxxx", self.obdobie)
        self.krycilist["A34"].value = self.krycilist["A34"].value.replace("xx-xxxx", self.obdobie)
        if self.datum_vyplatenia:
            self.krycilist["A31"].value = self.krycilist["A31"].value.replace("xx.xx.xxxx", self.datum_vyplatenia)
            self.krycilist["A35"].value = self.krycilist["A35"].value.replace("xx.xx.xxxx", self.datum_vyplatenia)
        else:
            self.krycilist["A31"].value = self.krycilist["A31"].value.replace("xx.xx.xxxx", "- - -")
            self.krycilist["A35"].value = self.krycilist["A35"].value.replace("xx.xx.xxxx", "- - -")
        self.kstart = 5 #poloha počiatočnej bunky v hárku 'Krycí list',, inkrementovaná po každom zázname
        self.kpos = self.kstart
        self.kmax = 23 #max počet riadkov v krycom liste, inak sa pokazí formátovanie

        sum_row = self.vyplnit_harok_vypocet()

        # vyplnit harok Na vyplatenie
        vyplatit.merge_cells('A5:H5')
        vyplatit["A5"] = f"za obdobie '{self.obdobie}'"
        vyplatit["A5"].alignment = acenter

        vyplatit["A7"] = "Prevody spolu:"
        #vyplatit.merge_cells("B7:G7")
        vyplatit["B7"] = f"=Výpočet!G{sum_row}" 
        vyplatit[f"B7"].alignment = aleft
        vyplatit[f"B7"].font = self.fbold
        vyplatit["A8"] = "Z čísla účtu EnÚ:"
        vyplatit["B8"] = VyplatitAutorskeOdmeny.ucetEnÚ
        # Farba pozadia
        for i, rowOfCellObjects in enumerate(vyplatit['A7':'G8']):
            for n, cellObj in enumerate(rowOfCellObjects):
                cellObj.fill = PatternFill("solid", fgColor="FFFF00")

        #Litfond
        pos = 10
        a,b,c,d,e,f = range(pos, pos+6)
        vyplatit[f"A{a}"] = "Komu:"
        vyplatit[f"B{a}"] = f"Odvod Lit. fond ({VyplatitAutorskeOdmeny.litfond_odvod} %)"
        vyplatit[f"A{b}"] = "Názov:"
        vyplatit[f"B{b}"] = "Literárny fond"
        vyplatit[f"A{c}"] = "IBAN:"
        vyplatit[f"B{c}"] = VyplatitAutorskeOdmeny.ucetLitFond
        vyplatit[f"A{d}"] = "VS:"
        vyplatit[f"B{d}"] = "2001"
        vyplatit[f"A{e}"] = "KS:"
        vyplatit[f"B{e}"] = "558"
        vyplatit[f"A{f}"] = "Suma na úhradu:"
        vyplatit[f"B{f}"] = f"=Výpočet!I{sum_row}"
        vyplatit[f"B{f}"].alignment = aleft
        vyplatit[f"B{f}"].font = self.fbold
        
        #daň
        pos += 7
        a,b,c,d,e,f = range(pos, pos+6)
        vyplatit[f"A{a}"] = "Komu:"
        vyplatit[f"B{a}"] = "Zrážková daň z odmeny"
        vyplatit[f"A{b}"] = "Názov:"
        vyplatit[f"B{b}"] = "Finančná správa"
        vyplatit[f"A{c}"] = "IBAN:"
        vyplatit[f"B{c}"] = VyplatitAutorskeOdmeny.ucetFin
        vyplatit[f"A{d}"] = "VS:"
        # predpokladáme, ze self.obdobie na tvar yyyy-mmxxx
        vyplatit[f"B{d}"] = f"1700{self.obdobie[5:7]}{self.obdobie[:4]}"
        vyplatit[f"A{e}"] = "Suma na úhradu:"
        vyplatit[f"B{e}"] = f"=Výpočet!K{sum_row}"
        vyplatit[f"B{e}"].alignment = aleft
        vyplatit[f"B{e}"].font = self.fbold

        # Farba pozadia
        for i, rowOfCellObjects in enumerate(vyplatit['A10':'G21']):
            for n, cellObj in enumerate(rowOfCellObjects):
                cellObj.fill = PatternFill("solid", fgColor="FDEADA")
        
        #nevyplácaní autori
        for i, autor in enumerate(self.suma_preplatok):
            self.import_rs_webrs(autor)
            self.po_autoroch(autor)

        #vyplácaní autori
        pos += 6
        for i, autor in enumerate(self.suma_vyplatit):
            self.import_rs_webrs(autor)
            self.po_autoroch(autor)
            self.kryci_list(autor, i)
            a,b,c,d,e,f = range(pos, pos+6)
            adata = OsobaAutor.objects.filter(rs_login=autor)[0]
            vyplatit[f"A{a}"] = "Komu:"
            vyplatit[f"B{a}"] = "Autor"
            vyplatit[f"A{b}"] = "Názov:"
            vyplatit[f"B{b}"] = self.meno_priezvisko(adata)
            vyplatit[f"A{c}"] = "IBAN:"
            vyplatit[f"B{c}"] = adata.bankovy_kontakt
            vyplatit[f"A{d}"] = "VS:"
            vyplatit[f"B{d}"] = self.obdobie
            vyplatit[f"A{e}"] = "KS:"
            vyplatit[f"B{e}"] = "3014"
            vyplatit[f"A{f}"] = "Suma na úhradu:"
            vyplatit[f"B{f}"] = f"=Výpočet!L{i+2}"
            vyplatit[f"B{f}"].alignment = aleft
            vyplatit[f"B{f}"].font = self.fbold
            pos += 7

        pos += 7
        a,b,c,d,e,f = range(pos, pos+6)
        vyplatit.merge_cells(f'A{a}:D{a}')
        vyplatit[f"A{a}"] = "Výpočet autorských odmien bol realizovaný softvérovo na základe údajov z redakčného systému Encyclopaedie Beliany"
        vyplatit[f"A{a}"].alignment = Alignment(wrapText=True, horizontal='left')
        vyplatit.row_dimensions[a].height = 30
        #vyplatit[f"A{a}"] = "Spracovala:"
        #vyplatit[f"B{a}"] = "M. Sekeráková"
        #vyplatit[f"B{b}"] = "sekretariát EnÚ CSČ SAV"

        #vyplatit[f"A{d}"] = "V Bratislave dňa {}".format(date.today().strftime("%d.%m.%Y"))
        if self.datum_vyplatenia:
            vyplatit[f"A{d}"] = "V Bratislave dňa {}".format(self.datum_vyplatenia)
        else:
            vyplatit[f"A{d}"] = "V Bratislave dňa {}".format(date.today().strftime("%d.%m.%Y"))
        vyplatit[f"A{d}"] = "V Bratislave dňa {}".format(date.today().strftime("%d.%m.%Y"))
        vyplatit[f"E{e}"] = "Ing. Tatiana Šrámková"
        vyplatit[f"E{f}"] = "vedúca org. zložky EnÚ CSČ SAV"
        vyplatit.print_area = f"A1:G{pos+7}"

        #suma v kryci_list
        self.krycilist[f"A{self.kpos}"] = "Spolu"
        self.krycilist[f"A{self.kpos}"].font = self.fbold
        self.krycilist[f"H{self.kpos}"] = f"=SUM(H{self.kstart}:H{self.kpos-1})"
        self.krycilist[f"H{self.kpos}"].font = self.fbold
        self.krycilist[f"I{self.kpos}"] = f"=SUM(I{self.kstart}:I{self.kpos-1})"
        self.krycilist[f"I{self.kpos}"].font = self.fbold
        self.krycilist[f"J{self.kpos}"] = f"=SUM(J{self.kstart}:J{self.kpos-1})"
        self.krycilist[f"J{self.kpos}"].font = self.fbold
        self.krycilist[f"K{self.kpos}"] = f"=SUM(K{self.kstart}:K{self.kpos-1})"
        self.krycilist[f"K{self.kpos}"].font = self.fbold

        #Všetky súbory, ktoré majú byť uložené do DB, musia mať záznam logu, ktorú končí na 'uložené do súboru {fpath}'
        #if self.datum_vyplatenia and not self.negenerovat_subory:
        if self.datum_vyplatenia:
            fpath = os.path.join(za_mesiac,f"Vyplatene-{self.obdobie}.xlsx")
            workbook.save(fpath)
            msg = f"Údaje o vyplácaní boli uložené do súboru {fpath}"
            self.log(messages.SUCCESS, msg)
            #self.db_logger.warning(msg)

            # vytvorit csv subory na importovanie
            fpath = os.path.join(za_mesiac,f"Import-rs-{self.obdobie}.csv")
            with open(fpath, "w") as csvfile:
                csvWriter = csv.writer(csvfile, delimiter=',', quotechar='"')
                for b, c in zip(self.importrs["b:c"][0], self.importrs["b:c"][1]) :
                    csvWriter.writerow([b.value,c.value])
            msg = f"Údaje na importovanie do RS boli uložené do súboru {fpath}"
            self.log(messages.SUCCESS, msg)

            fpath = os.path.join(za_mesiac,f"Import-webrs-{self.obdobie}.csv")
            with open(fpath, "w") as csvfile:
                csvWriter = csv.writer(csvfile, delimiter=',', quotechar='"')
                for b, c in zip(self.importwebrs["b:c"][0], self.importwebrs["b:c"][1]) :
                    csvWriter.writerow([b.value,c.value])
            msg = f"Údaje na importovanie do WEBRS boli uložené do súboru {fpath}"
            self.log(messages.SUCCESS, msg)
        else:
            fpath = os.path.join(za_mesiac,f"Vyplatit-{self.obdobie}-THS.xlsx")
            #if not self.negenerovat_subory:
                #workbook.save(fpath)
                #msg = f"Údaje o vyplácaní na odoslanie THS boli uložené do súboru {fpath}"
                #self.log(messages.WARNING, msg)
                #self.db_logger.warning(msg)
            workbook.save(fpath)
            msg = f"Údaje o vyplácaní na odoslanie THS boli uložené do súboru {fpath}"
            self.log(messages.SUCCESS, msg)
            #self.db_logger.warning(msg)

    # vyplnit harok vypocet
    def vyplnit_harok_vypocet(self):
        #hlavicka
        vypocet_hlavicka = ["Autor", "Zmluvy", "Zmluva o nezdaňovaní", "Rezident SR", "Honorár", "Preplatok", "Honorár – Preplatok", "Odvod LF", "Odvod LF zaokr.", f"{VyplatitAutorskeOdmeny.dan_odvod} % daň", "daň zaokr.", "Vyplatiť"]

        for i, val in enumerate(vypocet_hlavicka):
            self.vypocet.cell(row=1, column=i+1).value = vypocet_hlavicka[i]
            self.vypocet.cell(row=1, column=i+1).font = self.fbold
            self.vypocet.cell(row=1, column=i+1).alignment = Alignment(wrapText=True, horizontal='center')  
            self.vypocet.column_dimensions[get_column_letter(i+1)].width = 14
        self.vypocet.column_dimensions["A"].width = 20
        self.vypocet.row_dimensions[1].height = 30

        #zapísať údaje na vyplatenie
        for i, autor in enumerate(self.suma_vyplatit):
            adata = OsobaAutor.objects.filter(rs_login=autor)[0]
            ii = i+2
            self.vypocet[f"A{ii}"] = autor
            self.vypocet[f"B{ii}"] = self.suma_vyplatit[autor][2 ]
            self.vypocet[f"B{ii}"].alignment = Alignment(wrapText=True, horizontal='center')
            # Uvádzame, či je podpísaná zmluva o nezdaňovaní, čiže opak adata.zdanit
            self.vypocet[f"C{ii}"] = "ano" if self.zmluva_nezdanit(adata) else "nie"
            self.vypocet[f"C{ii}"].alignment = self.aright
            self.vypocet[f"C{ii}"].alignment = Alignment(wrapText=True, horizontal='center')
            # Pole "rezident SR", použije sa na Vúpočet odvody LF a dane: 
            # odvod LF: zákov Zákon č. 13/1993 Z. z.  Zákon Národnej rady Slovenskej republiky o umeleckých fondoch
            # odvádzajú sa 2 %, ak je trvalé bydlisko v SR
            # odvádza sa aj v prípade dedičov (vtedy je to "preddavok", čo nás ale nezaujíma)
            # Podľa zmluvy  ČR ttps://www.slov-lex.sk/pravne-predpisy/SK/ZZ/2003/238/20030714
            # sa licenčné poplatky zdaňujú v štáte rezidencie. Daň teda neodvádzame.  
            self.vypocet[f"D{ii}"] = "ano" if self.je_rezident(adata) else "nie"
            self.vypocet[f"D{ii}"].alignment = Alignment(wrapText=True, horizontal='center')
            self.vypocet[f"E{ii}"] = round(self.suma_vyplatit[autor][0],2)
            self.vypocet[f"F{ii}"] = self.suma_vyplatit[autor][1]
            self.vypocet[f"G{ii}"] = f"=E{ii}-F{ii}"
            #self.vypocet[f"H{ii}"] = f"=G{ii}*0.02"
            self.vypocet[f"H{ii}"] = f'=IF(D{ii}="ano",G{ii}*{VyplatitAutorskeOdmeny.litfond_odvod/100},0'
            #zaokrúhľovanie: https://podpora.financnasprava.sk/407328-Sp%C3%B4sob-zaokr%C3%BAh%C4%BEovania-v-roku-2020
            self.vypocet[f"I{ii}"] = f"=ROUND(H{ii},2)"
            #self.vypocet[f"J{ii}"] = f"=(G{ii}-I{ii})*{VyplatitAutorskeOdmeny.dan_odvod/100}"
            #self.vypocet[f"J{ii}"] = f'=IF(C{ii}="ano",(G{ii}-I{ii})*{VyplatitAutorskeOdmeny.dan_odvod/100},0'
            self.vypocet[f"J{ii}"] = f'=IF(AND(C{ii}="nie",D{ii}="ano"),(G{ii}-I{ii})*{VyplatitAutorskeOdmeny.dan_odvod/100},0'
            self.vypocet[f"K{ii}"] = f"=ROUND(J{ii},2)"
            self.vypocet[f"L{ii}"] = f"=G{ii}-I{ii}-K{ii}"
        pass
        self.vypocet[f"A{ii+1}"] = "Na úhradu"
        self.vypocet[f"G{ii+1}"] = f"=SUM(G2:G{ii})"
        self.vypocet[f"I{ii+1}"] = f"=SUM(I2:I{ii})"
        self.vypocet[f"K{ii+1}"] = f"=SUM(K2:K{ii})"
        self.vypocet[f"L{ii+1}"] = f"=SUM(L2:L{ii})"
        for i, val in enumerate(vypocet_hlavicka):
            self.vypocet.cell(row=ii+1, column=i+1).font = self.fbold
        return ii+1 #vratit riadok so suctami

    def odviest_dan(self, adata): 
        return self.je_rezident(adata) and adata.zdanit == "ano"

    # LF sa odvádza, len ak má autor trvalé bydlisko v SR
    def odviest_lf(self, adata): 
        return adata.adresa_stat == "Slovenská republika"

    def je_rezident(self, adata):
        return adata.rezident == "ano"

    def zmluva_nezdanit(self, adata):
        return adata.zdanit != "ano"

    # zapíše údaje o platbe do hárkov Import RS a Import Webrs
    def import_rs_webrs(self, autor):
        if not self.datum_vyplatenia: return
        for rstype in self.data[autor]:
            if rstype=="rs":
                ws = self.importrs
                pos = self.rpos
            else:
                ws = self.importwebrs
                pos = self.wpos
            for zmluva in self.data[autor][rstype]:
                for heslo in self.data[autor][rstype][zmluva]:
                    link, lname = re.findall(r'"([^"]*)"',heslo[2]) 
                    ws[f"A{pos}"].hyperlink = link
                    ws[f"A{pos}"].value = lname
                    ws[f"A{pos}"].style = "Hyperlink"
                    ws[f"B{pos}"] = link.split("/")[-1]   #nid
                    ws[f"C{pos}"] = self.datum_vyplatenia
                    pos += 1
            if rstype=="rs":
                self.rpos = pos
            else:
                self.wpos = pos

    # zapíše údaje o platbe do hárku 'Krycí list'
    def kryci_list(self, autor, ind):
        adata = OsobaAutor.objects.filter(rs_login=autor)[0]
        self.krycilist[f"A{self.kpos}"].value = self.meno_priezvisko(adata)
        self.krycilist[f"D{self.kpos}"].value = adata.rodne_cislo
        self.krycilist[f"F{self.kpos}"].value = f"=Výpočet!B{ind+2}" 
        self.krycilist[f"H{self.kpos}"].value = f"=Výpočet!G{ind+2}"    #brutto
        self.krycilist[f"I{self.kpos}"].value = f"=Výpočet!K{ind+2}"    #daň
        self.krycilist[f"J{self.kpos}"].value = f"=Výpočet!I{ind+2}"    #LitFond
        self.krycilist[f"K{self.kpos}"].value = f"=Výpočet!L{ind+2}"    #netto
        self.kpos += 1

    # zapíše údaje o platbe do hárku Po autoroch
    def po_autoroch(self, autor):
        if not self.po_autoroch: return
        ws = self.poautoroch
        for col in range(1,8):
            ws.column_dimensions[get_column_letter(col)].width = 10
        ws.column_dimensions["D"].width = 14
        ws.column_dimensions["E"].width = 14
        vyplaca_sa = False
        if autor in self.suma_vyplatit:
            vyplaca_sa = True
            honorar, preplatok, zmluvy = self.suma_vyplatit[autor]
        else:
            honorar, preplatok, zmluvy = self.suma_preplatok[autor]
        honorar = round(honorar,2)

        ftitle = Font(name="Arial", bold=True, size='14')

        ws.merge_cells(f'A{self.ppos}:H{self.ppos}')
        ws[f'A{self.ppos}'] = f"Vyplatenie autorského honorára za obdobie {self.obdobie}"
        ws[f"A{self.ppos}"].alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[self.ppos].height = 70
        ws[f"A{self.ppos}"].font = ftitle
        self.ppos += 1  


        adata = OsobaAutor.objects.filter(rs_login=autor)[0]
        self.bb( "Meno:" , self.meno_priezvisko(adata))
        self.bb( "Používateľské meno v RS / WEBRS:" , autor)
        self.bb( "E-mail:" , adata.email)
        self.bb( "Účet:", adata.bankovy_kontakt)
        self.bb( "Dátum vytvorenia zápisu:" , date.today().strftime("%d.%m.%Y"))
        # na uloženie do databázy:
        vdata = {
                "preplatok0":preplatok, # počiatočný preplatok
                "honorar":0,             # round(honorar_rs+honorar_webrs)
                "honorar_rs":0,
                "honorar_webrs":0,
                "znaky_rs":0,
                "znaky_webrs":0,
                "lf":0,                 # odvod litfond
                "dan":0,                # dan
                "vyplatit":0,           # suma vyplatená autorovi
                "zmluva":set()          # zmluvy, podľa ktorých sa vyplácalo
                }
        
        self.bb( "Preplatok predchádzajúcich platieb:", preplatok)
        self.bb( "Honorár za aktuálne obdobie:", honorar)
        vdata["honorar"] = honorar
        if vyplaca_sa:
            if preplatok > 0:
                vypocet = honorar-preplatok
                self.bb( "Honorár – Preplatok:", vypocet)

                #LitFond
                if self.odviest_lf(adata):
                    lf = round((honorar-preplatok)*VyplatitAutorskeOdmeny.litfond_odvod/100,2)
                    vypocet -= lf
                    self.bb( f"Odvod LitFond ({VyplatitAutorskeOdmeny.litfond_odvod} %, zaokr.):", lf)
                else:
                    lf = 0
                    self.bb( f"Odvod LitFond (neodvádza sa, bydlisko mimo SR):", 0)
                
                #daň
                if not self.je_rezident(adata):
                    dan = 0
                    vyplatit = round(vypocet,2)
                    self.bb( f"Daň:", f"nezdanuje sa (nerezident, {adata.adresa_stat})")
                elif self.zmluva_nezdanit(adata):  
                    dan = 0
                    vyplatit = round(vypocet,2)
                    self.bb( f"Daň:", "nezdaňuje sa (podpísaná dohoda)")
                else:
                    dan = round(vypocet*VyplatitAutorskeOdmeny.dan_odvod/100,2)
                    vyplatit = round(vypocet - dan,2)
                    self.bb( f"Daň ({VyplatitAutorskeOdmeny.dan_odvod} %, zaokr.):", dan)

                self.bb( "Vyplatiť:", vyplatit)
                self.bb( "Nová hodnota preplatku:", 0)
                adata.preplatok = 0
                adata._change_reason = 'vyplacanie.py: preplatok znížený na 0 € (vyplácanie %s).'%self.obdobie
                vdata["lf"] = lf
                vdata["dan"] = dan
                vdata["vyplatit"] = vyplatit
                #adata.save()
            else:   #preplatok=0
                vypocet = honorar

                #LitFond
                if self.odviest_lf(adata):
                    lf = round(vypocet*VyplatitAutorskeOdmeny.litfond_odvod/100,2)
                    vypocet -= lf
                    self.bb( f"Odvod LitFond ({VyplatitAutorskeOdmeny.litfond_odvod} %, zaokr.):", lf)
                else:
                    lf = 0
                    self.bb( f"Odvod LitFond:", "neodvádza sa, bydlisko mimo SR")

                #daň
                if not self.je_rezident(adata):
                    dan = 0
                    vyplatit = round(vypocet,2)
                    self.bb( f"Daň:", f"nezdaňuje sa (nerezident, {adata.adresa_stat})")
                elif self.zmluva_nezdanit(adata):  
                    dan = 0
                    vyplatit = round(vypocet,2)
                    self.bb( f"Daň:", "nezdanuje sa (podpísaná dohoda)")
                else:
                    dan = round(vypocet*VyplatitAutorskeOdmeny.dan_odvod/100,2)
                    vyplatit = round(vypocet - dan,2)
                    self.bb( f"Daň ({VyplatitAutorskeOdmeny.dan_odvod} %, zaokr.):", dan)

                self.bb( "Vyplatiť:", vyplatit)
                vdata["lf"] = lf
                vdata["dan"] = dan
                vdata["vyplatit"] = vyplatit
            self.bb( "Dátum vyplatenia:", self.datum_vyplatenia)
        else:
                self.bb( "Vyplatiť:", 0)
                self.bb( "Nová hodnota preplatku:", preplatok - honorar)
                adata.preplatok = preplatok - honorar
                adata._change_reason = 'vyplacanie.py: preplatok znížený o %0.2f € na %0.2f € (vyplácanie %s).'%(honorar, preplatok - honorar, self.obdobie)
                #adata.save()
        self.ppos  += 1  

        ws.merge_cells(f'A{self.ppos}:H{self.ppos}')
        ws[f'A{self.ppos}'] = "Prehľad platieb po heslách"
        ws[f"A{self.ppos}"].alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[self.ppos].height = 40
        ws[f"A{self.ppos}"].font = ftitle
        self.ppos  += 1  

        #vypísať vyplatené heslá a zrátať výslednú sumu
        self.bb3(["Kniha/web","Zmluva","Heslo","Dátum zadania", "Suma [€/AH]","Počet znakov", "Vyplatiť [€]"],hdr=True)
        zdata = ZmluvaAutor.objects.filter(zmluvna_strana__rs_login=autor)
        zvyplatit = {}
        for zmluva in zdata:
            zvyplatit[zmluva.cislo_zmluvy] = zmluva.honorar_ah
        nitems = 0  #pocet hesiel
        for rstype in self.data[autor]:
            for zmluva in self.data[autor][rstype]:
                for heslo in self.data[autor][rstype][zmluva]:
                    if rstype=="rs":
                        self.bb3(["kniha", zmluva , heslo[2], heslo[4], zvyplatit[zmluva], heslo[0]])
                        vdata["honorar_rs"] += zvyplatit[zmluva] * heslo[0] / 36000 
                        vdata["znaky_rs"] += heslo[0]
                        vdata["zmluva"].add(zmluva)
                    else:
                        self.bb3(["web", zmluva , heslo[2], heslo[4], zvyplatit[zmluva], heslo[0]])
                        vdata["honorar_webrs"] += zvyplatit[zmluva] * heslo[0] / 36000 
                        vdata["znaky_webrs"] += heslo[0]
                        vdata["zmluva"].add(zmluva)
                    nitems += 1
        #round(round,...,3),2) kvoli nepresnosti float aritmetiky (0.499999999997 namiesto 0.5)
        vdata["honorar_webrs"] = round(round(vdata["honorar_webrs"],3),2)
        vdata["honorar_rs"] = round(round(vdata["honorar_rs"],3),2)
        #spočítať všetky sumy
        #stĺpec so sumou: H
        ws.merge_cells(f'A{self.ppos}:G{self.ppos}')
        if vyplaca_sa:
            ws[f'A{self.ppos}'] = "Honorár za heslá (vyplatí sa po odčítaní preplatku a odvodov)"
        else:
            ws[f'A{self.ppos}'] = "Honorár za heslá (nevyplatí sa, odpočíta sa z preplatku)"
        ws[f'A{self.ppos}'].font = self.fbold
        ws[f"H{self.ppos}"].alignment = Alignment(horizontal='right')
        ws[f'H{self.ppos}'] = "=SUM(H{}:H{}".format(self.ppos-nitems,self.ppos-1) 
        ws[f'H{self.ppos}'].font = self.fbold
        ws[f"H{self.ppos}"].number_format= "0.00"
        self.ppos  += 2  
        ws.merge_cells(f'A{self.ppos}:F{self.ppos}')
        ws[f"A{self.ppos}"] = "Výpočet autorských odmien bol realizovaný softvérovo na základe údajov z redakčného systému Encyclopaedie Beliany"
        ws[f"A{self.ppos}"].alignment = Alignment(wrapText=True, horizontal='left')
        ws.row_dimensions[self.ppos].height = 30
        self.ppos  += 2  

        #aktualizovať záznam v databáze
        self.aktualizovat_db(adata, vdata)

        #insert page break
        page_break = Break(id=self.ppos-1)  # create Break obj
        ws.row_breaks.append(page_break)  # insert page break
        pass

    def aktualizovat_db(self, adata, vdata):
        if not self.datum_vyplatenia: return
        adata.save()
        platba = PlatbaAutorskaOdmena.objects.create( 
            datum_uhradenia = re.sub(r"([^.]*)[.]([^.]*)[.](.*)", r"\3-\2-\1", self.datum_vyplatenia),
            uhradena_suma = round(vdata['vyplatit'], 2),
            preplatok_pred = round(vdata['preplatok0'], 2) ,
            obdobie = self.obdobie, 
            zmluva = ', '.join(vdata['zmluva']), 
            autor = adata, 
            honorar = vdata['honorar'], 
            #round(round,...,3),2) kvoli nepresnosti float aritmetiky (0.499999999997 namiesto 0.5)
            honorar_rs = round(round(vdata["honorar_rs"],3),2),
            honorar_webrs = round(round(vdata["honorar_webrs"],3),2),
            znaky_rs =  vdata['znaky_rs'],
            znaky_webrs =  vdata['znaky_webrs'],
            odvod_LF = round(vdata['lf'], 2), 
            odvedena_dan = round(vdata['dan'], 2),
            preplatok_po = round(adata.preplatok, 2) 
            )
        pass

    def bb(self, v1, v2):
        ws = self.poautoroch
        ws.merge_cells(f'A{self.ppos}:D{self.ppos}')
        ws.merge_cells(f'E{self.ppos}:H{self.ppos}')
        ws[f"A{self.ppos}"] = v1
        ws[f"E{self.ppos}"] = v2
        ws[f"E{self.ppos}"].alignment = Alignment(horizontal='left')
        ws.row_dimensions[self.ppos].height = 16
        self.ppos  += 1  

    def bb3(self, items, hdr=False):
        col="ABCDEFGHIJK"
        ws = self.poautoroch

        nc = 0
        acenter = Alignment(horizontal='center')
        if hdr:
            ws.row_dimensions[self.ppos].height = 30
            for n, item in enumerate(items):
                ws[f"{col[n+nc]}{self.ppos}"].font = self.fbold
                ws[f"{col[n+nc]}{self.ppos}"].alignment = Alignment(wrapText=True, horizontal='center')
                ws[f"{col[n+nc]}{self.ppos}"] = item
                if type(item) is str and "Heslo" in item:
                    ws.merge_cells(f'{col[n]}{self.ppos}:{col[n+1]}{self.ppos}')
                    nc = 1
        else:
            nc = 0
            for n, item in enumerate(items):
                if type(item) is str and "HYPERLINK" in item:
                    #=HYPERLINK("https://rs.beliana.sav.sk/node/218406";"langusta")
                    link, lname = re.findall(r'"([^"]*)"',item) 
                    ws[f"{col[n+nc]}{self.ppos}"].alignment = acenter
                    ws.merge_cells(f'{col[n]}{self.ppos}:{col[n+1]}{self.ppos}')
                    nc = 1
                    ws[f"{col[n]}{self.ppos}"].hyperlink = link
                    ws[f"{col[n]}{self.ppos}"].value = lname
                    ws[f"{col[n]}{self.ppos}"].style = "Hyperlink"
                else:
                    ws[f"{col[n+nc]}{self.ppos}"] = item
                    ws[f"{col[n+nc]}{self.ppos}"].alignment = acenter
            # suma za heslo, posledné 2 položky sú suma/AH a počet znakov
            ws[f"{col[n+nc]}{self.ppos}"].alignment = Alignment(horizontal='right')
            #ws[f"{col[n+nc+1]}{self.ppos}"] = f"={col[n+nc-1]}{self.ppos}*{col[n+nc]}{self.ppos}/36000"
            ws[f"{col[n+nc+1]}{self.ppos}"].value = round(items[-2]*items[-1]/36000,2)
            ws[f"{col[n+nc+1]}{self.ppos}"].alignment = Alignment(horizontal='right')
            #ws[f"{col[n+nc+1]}{self.ppos}"].style.number_format= numbers.NumberFormat.FORMAT_NUMBER_00
            ws[f"{col[n+nc+1]}{self.ppos}"].number_format= "0.00"
            ws.row_dimensions[self.ppos].height = 16
        self.ppos  += 1  

    def zrusit_vyplacanie(self, za_mesiac):
        platby = PlatbaAutorskaOdmena.objects.filter(obdobie=za_mesiac)
        for platba in platby:
            #vrátit hodnotu preplatku
            msg = f"Platba za autora {platba.autor.rs_login} za obdobie {za_mesiac} bola odstránená z databázy"
            vratit = platba.preplatok_pred-platba.preplatok_po
            platba.autor.preplatok += vratit
            if vratit > 0.01:
                platba.autor._change_reason = 'vyplacanie.py: zrušené vyplácanie %s, preplatok zvýšený o %0.2f € na %0.2f €.'%(za_mesiac, vratit, platba.autor.preplatok)
            platba.autor.save()
            #zmazať platbu
            platba.delete()
            self.log(messages.SUCCESS, msg)

