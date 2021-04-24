import csv
from django.core.management import BaseCommand, CommandError
from zmluvy.models import OsobaAutor, ZmluvaAutor
from zmluvy.common import transliterate
from django.utils import timezone
from ipdb import set_trace as trace
from collections import defaultdict
from openpyxl import load_workbook
from openpyxl.styles import Font, Color, colors, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.pagebreak import Break
from glob import glob

# 1. a 2. stlpec: uid a login autorov v RS
# 3. stlpec: Autori uvedení ako autori hesiel

ws_template = "data/Sablony/UhradaAutHonoraru.xlsx"
ah_cesta = "data/Vyplacanie_autorskych_honorarov"
litfond_odvod = 0.02
min_znakov=2000     #minimálny počet znakov na vyplatenie 
ucetEnÚ = "SK36 8180 0000 0070 0061 8734 - Beliana"
ucetLITA  = "SK47 0200 0000 0012 2545 9853" 
ucetFin = "SK61 8180 5002 6780 2710 3305"



class Command(BaseCommand):
    help = 'Vygenerovať podklady na vyplácanie autorských odmien'

    def add_arguments(self, parser):
        parser.add_argument('--na-vyplatenie', type=str, help="Priečinok s názvom RRRR-MM so súbormi s údajmi pre vyplácanie autorských honorárov")

    def nacitat_udaje_grafik(self, fname):
        pass

    def hlavicka_test(self, fname, row):
        # povinné stĺpce v csv súbore:
        povinne = ["Nid", "Autorská zmluva", "Vyplatenie odmeny", "Dĺžka autorom odovzdaného textu", "Dátum záznamu dĺžky", "Dátum vyplatenia"]
        for item in povinne:
            if not item in row:
                self.stdout.write(self.style.ERROR(f"Súbor {fname} musí obsahovať stĺpec '{item}'"))
                return False
        if not "Login" in row :
            if not "Meno" in row or not "Priezvisko" in row: 
                trace()
                self.stdout.write(self.style.ERROR(f"Súbor {fname} musí obsahovať stĺpec 'Login' alebo stĺpce 'Meno' a 'Prezvisk'o"))
                return False
        return True

    def nacitat_udaje_autor(self, fname, rs_webrs):
        hdr = {}
        with open(fname, 'rt') as f:
            reader = csv.reader(f, dialect='excel')
            hdrOK = False
            hasLogin = False
            for row in reader:
                if not hdrOK:
                    if not self.hlavicka_test(fname, row):
                        self.stdout.write(self.style.ERROR(f"Nesprávny súbor {fname}"))
                        raise SystemExit
                    for n, ii in enumerate(row):
                        hdr[ii]=n
                    if "Login" in row: hasLogin=True
                    hdrOK = True
                if row[hdr["Vyplatenie odmeny"]] == "Heslo vypracoval autor, vyplatiť" and not row[hdr["Dátum vyplatenia"]]:
                    if hasLogin:
                        login = row[hdr["Login"]]
                    else:
                        login = transliterate(row[hdr["Priezvisko"]])+transliterate(row[hdr["Meno"]])
                    if not login in self.autori_pocet_znakov: self.autori_pocet_znakov[login] = 0 
                    self.autori_pocet_znakov[login] += int(row[hdr["Dĺžka autorom odovzdaného textu"]])
                    self.autori_udaje[login].append(row + [rs_webrs])
        # vratit hdr, aby bolo mozne porovnanie
        return hdr

    def meno_priezvisko(self, autor):
        mp = f"{autor.titul_pred_menom} {autor.meno} {autor.priezvisko}"
        if autor.titul_za_menom:
            mp = f"{mp}, {autor.titul_za_menom}"
        return mp

    def handle(self, *args, **kwargs):
        if kwargs['na_vyplatenie']:
            za_mesiac = kwargs['na_vyplatenie']
        else:
            self.stdout.write(self.style.ERROR(f"Nebol zadaný názov priečinka v {ah_cesta} s údajmi na vyplatenie"))
            raise SystemExit

        #najst csv subory 
        csv_subory = glob(f"{za_mesiac}/*.csv")
        self.autori_pocet_znakov = {}
        self.autori_udaje=defaultdict(list)
        self.hdr = None

        for csv_subor in csv_subory:
            print(csv_subor)
            if "_rs" in csv_subor:
                hdr = self.nacitat_udaje_autor(csv_subor, "rs")
            elif "_webrs" in csv_subor:
                hdr = self.nacitat_udaje_autor(csv_subor, "webrs")
            elif "_grafik" in csv_subor:
                self.nacitat_udaje_grafik(csv_subor)
                pass
            else:
                aux_name = csv_subor.split("/")[-1]
                self.stdout.write(self.style.ERROR(f"V priečinku {ah_cesta}/{za_mesiac} bol nájdený neznámy súbor {aux_name}"))
                self.stdout.write(self.style.ERROR("Súbor odstráňte alebo opravte jeho názov"))
                raise SystemExit
        autori_na_vyplatenie=[]
        trace()
        for autor in self.autori_pocet_znakov:
            if self.autori_pocet_znakov[autor]<min_znakov: 
                self.stdout.write(self.style.WARNING(f"Autor {autor}: nebude vyplatený pre malý počet znakov ({self.autori_pocet_znakov[autor]}) "))
                continue
            # spanning relationship: zmluvna_strana->rs_login
            o_query_set = ZmluvaAutor.objects.filter(zmluvna_strana__rs_login=autor)
            if o_query_set:
                self.stdout.write(self.style.SUCCESS(f"Autor {autor}: bude vyplatených {self.autori_pocet_znakov[autor]} znakov "))
                autori_na_vyplatenie.append(autor)
            else:
                self.stdout.write(self.style.ERROR(f"V databáze nebol nájdený záznam o zmluve pre autora {autor} "))
        pass
        # styly buniek, https://openpyxl.readthedocs.io/en/default/styles.html
        # default font dokumentu je Arial
        fbold = Font(name="Arial", bold=True)
        aright = Alignment(horizontal='right')
        acenter = Alignment(horizontal='center')
        aleft = Alignment(horizontal='left')

        workbook = load_workbook(filename=ws_template)
        vyplatit = workbook[workbook.sheetnames[0]]
        vypocet = workbook[workbook.sheetnames[1]]

        # vyplnit harok vypocet
        #hlavicka
        vypocet_hlavicka = ["Autor", "Odmena/AH", "Odviesť daň", "Počet znakov", "Odmena", "2% LF", "LF zaokr.", "19% daň", "daň zaokr.", "Vyplatiť"]

        for i, val in enumerate(vypocet_hlavicka):
            vypocet.cell(row=1, column=i+1).value = vypocet_hlavicka[i]
            vypocet.cell(row=1, column=i+1).font = fbold
            vypocet.column_dimensions[get_column_letter(i+1)].width = 14
        vypocet.column_dimensions[get_column_letter(1)].width = 20
        #zapisat udaje na vyplatenie
        for i, autor in enumerate(autori_na_vyplatenie):
            zdata = ZmluvaAutor.objects.filter(zmluvna_strana__rs_login=autor)[0]
            adata = OsobaAutor.objects.filter(rs_login=autor)[0]
            ii = i+2
            vypocet[f"A{ii}"] = autor
            vypocet[f"B{ii}"] = zdata.odmena
            vypocet[f"C{ii}"] = adata.zdanit if adata.zdanit else 'ano'
            vypocet[f"C{ii}"].alignment = aright
            vypocet[f"D{ii}"] = self.autori_pocet_znakov[autor]
            vypocet[f"E{ii}"] = f"=D{ii}*B{ii}/36000"
            #vypocet[f"F{ii}"] = f"=E{ii}*0.02"
            vypocet[f"F{ii}"] = f'=IF(C{ii}="ano",E{ii}*{litfond_odvod},0'
            vypocet[f"G{ii}"] = f"=ROUNDDOWN(F{ii},2)"
            #vypocet[f"H{ii}"] = f"=(E{ii}-G{ii})*0.19"
            vypocet[f"H{ii}"] = f'=IF(C{ii}="ano",(E{ii}-G{ii})*0.19,0'
            vypocet[f"I{ii}"] = f"=ROUNDDOWN(H{ii},2)"
            vypocet[f"J{ii}"] = f"=E{ii}-G{ii}-I{ii}"
        pass
        vypocet[f"A{ii+1}"] = "Na úhradu#"
        vypocet[f"E{ii+1}"] = f"=SUM(E2:E{ii})"
        vypocet[f"G{ii+1}"] = f"=SUM(G2:G{ii})"
        vypocet[f"I{ii+1}"] = f"=SUM(I2:I{ii})"
        vypocet[f"J{ii+1}"] = f"=SUM(J2:J{ii})"
        for i, val in enumerate(vypocet_hlavicka):
            vypocet.cell(row=ii+1, column=i+1).font = fbold
        #vypocet.freeze_panes = "A2"

        # vyplnit harok Na vyplatenie
        vyplatit.merge_cells('A5:G5')
        vyplatit["A5"] = "za obdobie '{}'".format(za_mesiac.split("/")[-1])
        vyplatit["A5"].alignment = acenter

        vyplatit["A7"] = "Odmena:"
        #vyplatit.merge_cells("B7:G7")
        vyplatit["B7"] = f"=Výpočet!E{ii+1}" 
        vyplatit[f"B7"].alignment = aleft
        vyplatit[f"B7"].font = fbold
        vyplatit["A8"] = "Z čísla účtu EnÚ:"
        vyplatit["B8"] = ucetEnÚ

        #Litfond
        pos = 10
        a,b,c,d,e,f = range(pos, pos+6)
        vyplatit[f"A{a}"] = "Komu:"
        vyplatit[f"B{a}"] = "2% z odmeny"
        vyplatit[f"A{b}"] = "Názov:"
        vyplatit[f"B{b}"] = "Literárny fond"
        vyplatit[f"A{c}"] = "IBAN:"
        vyplatit[f"B{c}"] = ucetLITA
        vyplatit[f"A{d}"] = "VS:"
        vyplatit[f"B{d}"] = "2001"
        vyplatit[f"A{e}"] = "KS:"
        vyplatit[f"B{e}"] = "558"
        vyplatit[f"A{f}"] = "Suma na úhradu:"
        vyplatit[f"B{f}"] = f"=Výpočet!G{ii+1}"
        vyplatit[f"B{f}"].alignment = aleft
        vyplatit[f"B{f}"].font = fbold
        
        #daň
        pos += 7
        a,b,c,d,e,f = range(pos, pos+6)
        vyplatit[f"A{a}"] = "Komu:"
        vyplatit[f"B{a}"] = "Zrážková daň z odmeny"
        vyplatit[f"A{b}"] = "Názov:"
        vyplatit[f"B{b}"] = "Finančná správa"
        vyplatit[f"A{c}"] = "IBAN:"
        vyplatit[f"B{c}"] = ucetFin
        vyplatit[f"A{d}"] = "VS:"
        vyplatit[f"B{d}"] = "2001"
        vyplatit[f"A{e}"] = "Suma na úhradu:"
        vyplatit[f"B{e}"] = f"=Výpočet!I{ii+1}"
        vyplatit[f"B{e}"].alignment = aleft
        vyplatit[f"B{e}"].font = fbold
        
        #autori
        pos += 6
        for i, autor in enumerate(autori_na_vyplatenie):
            a,b,c,d,e,f = range(pos, pos+6)
            zdata = ZmluvaAutor.objects.filter(zmluvna_strana__rs_login=autor)[0]
            adata = OsobaAutor.objects.filter(rs_login=autor)[0]
            vyplatit[f"A{a}"] = "Komu:"
            vyplatit[f"B{a}"] = "Autor"
            vyplatit[f"A{b}"] = "Názov:"
            vyplatit[f"B{b}"] = self.meno_priezvisko(adata)
            vyplatit[f"A{c}"] = "IBAN:"
            vyplatit[f"B{c}"] = adata.bankovy_kontakt
            vyplatit[f"A{d}"] = "VS:"
            vyplatit[f"B{d}"] = za_mesiac.split("/")[-1]
            vyplatit[f"A{e}"] = "KS:"
            vyplatit[f"B{e}"] = "3014"
            vyplatit[f"A{f}"] = "Suma na úhradu:"
            vyplatit[f"B{f}"] = f"=Výpočet!J{i+2}"
            vyplatit[f"B{f}"].alignment = aleft
            vyplatit[f"B{f}"].font = fbold
            pos += 7

        pos += 7
        a,b,c,d,e,f = range(pos, pos+6)
        vyplatit[f"A{a}"] = "Spracovala:"
        vyplatit[f"B{a}"] = "M. Sekeráková"
        vyplatit[f"B{b}"] = "sekretariát EnÚ CSČ SAV"

        vyplatit[f"A{d}"] = "V Bratislave dňa"
        vyplatit[f"E{e}"] = "Ing. Tatiana Šrámková"
        vyplatit[f"E{f}"] = "vedúca org. zložky EnÚ CSČ SAV"
        vyplatit.print_area = f"A1:G{pos+7}"

        workbook.save("xx.xlsx")

#row_number = 20  # the row that you want to insert page break
#page_break = Break(id=row_number)  # create Break obj
#ws.page_breaks.append(page_break)  # insert page break
