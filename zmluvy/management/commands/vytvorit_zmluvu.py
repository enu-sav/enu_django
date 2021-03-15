import csv
from django.core.management import BaseCommand, CommandError
from zmluvy.models import OsobaAutor, ZmluvaAutor
from django.utils import timezone
from ipdb import set_trace as trace

# 1. a 2. stlpec: uid a login autorov v RS
# 3. stlpec: Autori uvedení ako autori hesiel
sablona_name = "data/Sablony/AutorskaZmluva.fodt"

# konvertuje cislo v rvate XY0 do textoveho retazca
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

class Command(BaseCommand):
    help = 'Vytvorit autorsku zmluvu'

    def add_arguments(self, parser):
        parser.add_argument('--udaje-zmluvy', type=str, help="Údaje o zmluve v tvare 'LoginAutora,cislozmluvy,odmena'")
        parser.add_argument('--udaje-zmluvy-subor', type=str, help="Údaje o zmluvách v csv súbore so stĺpcami 'Číslo zmluvy,Meno,Priezvisko,Dohodnutá odmena'")

    def vytvorit_dokument(self, autor, login, cislozmluvy, odmena):
        # nacitat sablonu
        lt="&lt;"
        gt="&gt;"
        with open(sablona_name, "r") as f:
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
        nazov_zmluvy = f"{login}-{cislozmluvy.replace('/','-')}.fodt"
        with open(nazov_zmluvy, "w") as f:
            f.write(sablona)
        self.stdout.write(self.style.SUCCESS(f"Vytvorená zmluva: {nazov_zmluvy}"))

    # v databaze vytvorit alebo aktualizovat zaznam o zmluve
    def vytvorit_zmluvu(self, autor, login, cislozmluvy, odmena):
        #vytvorit zaznam o zmluve
        o_query_set = ZmluvaAutor.objects.filter(zmluvna_strana=autor)
        if o_query_set:
            zm = o_query_set.first()
            zm.zmluvna_strana = autor
            zm.odmena = odmena
            zm.cislo_zmluvy = cislozmluvy
            zm.datum_aktualizacie = timezone.now()
            zm.save()
            self.stdout.write(self.style.SUCCESS(f"V databáze bol aktualizovaný záznam o zmluve pre autora {login}"))
        else:
            zm = ZmluvaAutor.objects.create(
                zmluvna_strana = autor,
                odmena = odmena,
                cislo_zmluvy = cislozmluvy,
                datum_pridania = timezone.now(),
                datum_aktualizacie = timezone.now()
            )
            self.stdout.write(self.style.SUCCESS(f"V databáze bol vytvorený záznam o zmluve pre autora {login}"))

    def transliterate(self,text):
        ii= "'’,()[] ?,–_/.-aáäbcčdďeéěfghiíjklľĺmnňoóôöpqrŕřsštťuüúůvwxyýzžAÁÄBCČDĎEÉFGHIÍJKLĽĹMNŇOÓÔPQRŔŘSŠTŤUÜÚŮVWXYÝZŽ0123456789"
        oo= "-------__--_/.-aaabccddeeefghiijklllmnnoooopqrrrssttuuuuvwxyyzzAAABCCDDEEFGHIIJKLLLMNNOOOPQRRRSSTTUUUUVWXYYZZ0123456789"
        t=""
        for i,c in enumerate(text.strip(" ")):
            t += oo[ii.find(c)]
        return t

    #"Číslo zmluvy","Meno","Priezvisko","Dohodnutá odmena"
    def nacitat_zmluvy(self, fname):
        zmluvy=[]
        hdr = {}
        with open(fname, 'rt') as f:
            reader = csv.reader(f, dialect='excel')
            for row in reader:
                if row[0] == "Číslo zmluvy":
                    for n, ii in enumerate(row):
                        hdr[ii]=n
                    continue
                login = self.transliterate(row[hdr["Priezvisko"]])+self.transliterate(row[hdr["Meno"]])
                zmluvy.append([login, row[hdr["Číslo zmluvy"]], row[hdr["Dohodnutá odmena"]]])
        return zmluvy

    def handle(self, *args, **kwargs):
        if kwargs['udaje_zmluvy_subor']:
            zmluvy = self.nacitat_zmluvy(kwargs['udaje_zmluvy_subor'])
        elif kwargs['udaje_zmluvy']:
            zmluvy = [kwargs['udaje_zmluvy'].split(",")]

        for login, cislozmluvy, odmena in zmluvy:
            #nacitat data autora
            o_query_set = OsobaAutor.objects.filter(rs_login=login)
            if not o_query_set:
                self.stdout.write(self.style.ERROR(f"V databáze záznam pre {login} neexistuje."))
            elif len(o_query_set) > 1:
                self.stdout.write(self.style.ERROR(f"V databáze je pre {login} viac ako jeden záznam."))
            else:
                autor = o_query_set[0]
                self.vytvorit_dokument(autor, login, cislozmluvy, odmena)
                self.vytvorit_zmluvu(autor, login, cislozmluvy, odmena)
