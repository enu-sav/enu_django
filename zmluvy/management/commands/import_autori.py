import csv
from django.core.management import BaseCommand, CommandError
from zmluvy.models import OsobaAutor
import ipdb

# 1. a 2. stlpec: uid a login autorov v RS
# 3. stlpec: Autori uvedení ako autori hesiel
aa_name = "../../../data/aktivni_autori_2021-03-13.csv"
aa_name = "data/aktivni_autori_2021-03-13.csv"

class Command(BaseCommand):
    help = 'Načítať používateľov exportovaných z redakčného systému (role Autor, Konzultant a Garant)'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help="csv súbor s dátami o autoroch (generovaný zo zmlúv)")

    def read_aa(self):
        self.uids = {}
        self.aktivni_autori = []
        with open(aa_name, 'rt') as f:
            reader = csv.reader(f, dialect='excel')
            for row in reader:
                if row[0] == "Uid": continue
                self.uids[row[1]] = row[0]
                if len(row) > 2 and row[2]:
                    self.aktivni_autori.append(row[2])

    def read_author_data(self, path):
        ind = {}
        data = []
        with open(path, 'rt') as f:
            reader = csv.reader(f, dialect='excel')
            for row in reader:
                if row[0] == "Súbor": 
                    for n, ii in enumerate(row):
                        ind[ii]=n
                else:
                    data.append(row)
        return ind,data

    def transliterate(self,text):
        ii= "'’,()[] ?,–_/.-aáäbcčdďeéěfghiíjklľĺmnňoóôöpqrŕřsštťuüúůvwxyýzžAÁÄBCČDĎEÉFGHIÍJKLĽĹMNŇOÓÔPQRŔŘSŠTŤUÜÚŮVWXYÝZŽ0123456789"
        oo= "-------__--_/.-aaabccddeeefghiijklllmnnoooopqrrrssttuuuuvwxyyzzAAABCCDDEEFGHIIJKLLLMNNOOOPQRRRSSTTUUUUVWXYYZZ0123456789"
        t=""
        for i,c in enumerate(text.strip(" ")):
            t += oo[ii.find(c)]
        return t

    def handle(self, *args, **kwargs):
        self.read_aa()
        path = kwargs['path']
        hdr, data = self.read_author_data(path)
        self.stdout.write(self.style.SUCCESS('Path "%s"' % path))

        #"Súbor", "číslo zmluvy", "Titul pred", "Meno", "Priezvisko", "Titul za", "Adresa1", "Adresa2", "Adresa3", "Rodné číslo", "Dátum narodenia", "IBAN", "e-mail", "Odbor", "Dohodnutá odmena"
        for autor in data:
            login = self.transliterate(autor[hdr["Priezvisko"]])+self.transliterate(autor[hdr["Meno"]])
            if login in self.aktivni_autori:
                uid = self.uids[login]
                o_query_set = OsobaAutor.objects.filter(rs_uid=uid)
                if o_query_set:
                    oo = o_query_set[0]
                    oo.titul_pred_menom = autor[hdr["Titul pred"]]
                    oo.meno = autor[hdr["Meno"]]
                    oo.priezvisko = autor[hdr["Priezvisko"]]
                    oo.titul_za_menom = autor[hdr["Titul za"]]
                    oo.adresa_ulica = autor[hdr["Adresa1"]]
                    oo.adresa_mesto = autor[hdr["Adresa2"]]
                    oo.adresa_stat = autor[hdr["Adresa3"]]
                    oo.rodne_cislo = autor[hdr["Rodné číslo"]]
                    oo.bankovy_kontakt = autor[hdr["IBAN"]]
                    oo.email = autor[hdr["e-mail"]]
                    oo.odbor = autor[hdr["Odbor"]]
                    oo.save()
                else:   # create a new one
                    oo = OsobaAutor.objects.create(
                        rs_uid = uid,
                        rs_login = login,
                        titul_pred_menom = autor[hdr["Titul pred"]],
                        meno = autor[hdr["Meno"]],
                        priezvisko = autor[hdr["Priezvisko"]],
                        titul_za_menom = autor[hdr["Titul za"]],
                        adresa_ulica = autor[hdr["Adresa1"]],
                        adresa_mesto = autor[hdr["Adresa2"]],
                        adresa_stat = autor[hdr["Adresa3"]],
                        rodne_cislo = autor[hdr["Rodné číslo"]],
                        bankovy_kontakt = autor[hdr["IBAN"]],
                        email = autor[hdr["e-mail"]],
                        odbor = autor[hdr["Odbor"]],
                    )
                self.stdout.write(self.style.SUCCESS(f"OK: {login}"))
            else:
                self.stdout.write(self.style.ERROR(f"Nenájdené medzi aktívnymi autormi: {login}"))
