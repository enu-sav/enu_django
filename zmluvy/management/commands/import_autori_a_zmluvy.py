import csv, re
from django.core.management import BaseCommand, CommandError
from django.utils import timezone
from ipdb import set_trace as trace
from datetime import datetime

from zmluvy.models import OsobaAutor, AnoNie, ZmluvaAutor, StavZmluvy
from zmluvy.common import valid_iban

class Command(BaseCommand):
    help = 'Načítať používateľov a zmluvy (csv vytvorené z docx a pdf súborov)'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help="csv súbor s dátami o autoroch (generovaný zo zmlúv)")

    def read_author_data(self, path):
        ind = {}
        data = []
        with open(path, 'rt') as f:
            reader = csv.reader(f, dialect='excel')
            for row in reader:
                if row[1] == "Súbor": 
                    for n, ii in enumerate(row):
                        ind[ii]=n
                else:
                    data.append(row)
        return ind,data

    def transliterate(self,text):
        ii= "'’,()[] ?,–_/.-aáäbcčdďeéěfghiíjklľĺmnňoóôöpqrŕřsštťuüúůvwxyýzžAÁÄBCČDĎEÉFGHIÍJKLĽĹMNŇOÓÔPQRŔŘSŠTŤUÜÚŮVWXYÝZŽ0123456789"
        oo= "---------------aaabccddeeefghiijklllmnnoooopqrrrssttuuuuvwxyyzzAAABCCDDEEFGHIIJKLLLMNNOOOPQRRRSSTTUUUUVWXYYZZ0123456789"
        t=""
        for i,c in enumerate(text.strip(" ")):
            t += oo[ii.find(c)]
        return t.replace("-","")

    def handle(self, *args, **kwargs):
        path = kwargs['path']
        hdr, data = self.read_author_data(path)
        self.stdout.write(self.style.SUCCESS('Path "%s"' % path))
        #"#","Súbor","číslo zmluvy","Titul pred","Meno","Priezvisko","Titul za","Adresa1","Adresa2","Adresa3","Rodné číslo","IBAN","e-mail","Odbor","Dohodnutá odmena","Dátum CRZ","Url zmluvy","Zdaniť","Zomrel"

        for autor in data:
            login = self.transliterate(autor[hdr["Priezvisko"]])+self.transliterate(autor[hdr["Meno"]])
            if autor[hdr["IBAN"]] and not valid_iban(autor[hdr["IBAN"]]):
                self.stdout.write(self.style.ERROR(f"chybný IBAN: {login} {autor[hdr['číslo zmluvy']]} {autor[hdr['IBAN']]}"))
            o_query_set = OsobaAutor.objects.filter(rs_login=login)
            if o_query_set:
                oo = o_query_set[0]
                if autor[hdr["Titul pred"]]: oo.titul_pred_menom = autor[hdr["Titul pred"]]
                oo.meno = autor[hdr["Meno"]]
                oo.priezvisko = autor[hdr["Priezvisko"]]
                if autor[hdr["Titul za"]]: 
                    oo.titul_za_menom = autor[hdr["Titul za"]]
                if autor[hdr["Adresa1"]]: 
                    oo.adresa_ulica = autor[hdr["Adresa1"]]
                if autor[hdr["Adresa2"]]: 
                    oo.adresa_mesto = autor[hdr["Adresa2"]]
                if autor[hdr["Adresa3"]]: 
                    oo.adresa_stat = autor[hdr["Adresa3"]]
                if autor[hdr["Rodné číslo"]]: 
                    oo.rodne_cislo = autor[hdr["Rodné číslo"]]
                if autor[hdr["IBAN"]]: 
                    oo.bankovy_kontakt = autor[hdr["IBAN"]]
                if autor[hdr["e-mail"]]: 
                    oo.email = autor[hdr["e-mail"]]
                if autor[hdr["Odbor"]]: 
                    oo.odbor = autor[hdr["Odbor"]]
                if autor[hdr["Zomrel"]]:
                    oo.poznamka = "Autor zomrel"
                if autor[hdr["Zdaniť"]] == "nie":
                    oo.zdanit = AnoNie.NIE
                else:
                    oo.zdanit = AnoNie.ANO
                if autor[hdr["Preplatok"]]:
                    oo.preplatok = autor[hdr["Preplatok"]].replace(",",".")
                if autor[hdr["Url zmluvy"]]:
                    oo.url_zmluvy = autor[hdr["Url zmluvy"]]
                oo.save()

                # pridať zmluvu
                if autor[hdr["číslo zmluvy"]]:
                    o_query_set = ZmluvaAutor.objects.filter(zmluvna_strana=oo)
                    self.stdout.write(self.style.SUCCESS(f"OK: {login}, zmluva {autor[hdr['číslo zmluvy']]}"))
                    # zistiť, či už zmluvu máme
                    zm = None
                    for zz in o_query_set:
                        if zz.cislo_zmluvy == autor[hdr["číslo zmluvy"]]:
                            zm = zz
                            break
                    if zm:
                        continue

                    zm = ZmluvaAutor.objects.create(zmluvna_strana=oo)
                    zm.odmena_ah = autor[hdr["Dohodnutá odmena"]]
                    zm.cislo_zmluvy = autor[hdr["číslo zmluvy"]]

                    if autor[hdr["Dátum CRZ"]] and autor[hdr["Url zmluvy"]]:
                        #zm.datum_zverejnenia_CRZ = autor[hdr["Dátum CRZ"]]
                        if "-" in autor[hdr["Dátum CRZ"]]:
                            zm.datum_zverejnenia_CRZ = datetime.strptime(autor[hdr["Dátum CRZ"]],"%Y-%m-%d")
                        else:
                            zm.datum_zverejnenia_CRZ = datetime.strptime(autor[hdr["Dátum CRZ"]],"%d.%m.%Y")
                        zm.url_zmluvy = autor[hdr["Url zmluvy"]]
                        zm.stav_zmluvy = StavZmluvy.ZVEREJNENA_V_CRZ
                    datum_pridania = timezone.now()
                    zm.datum_aktualizacie = timezone.now()
                    zm.save()
                else:
                    self.stdout.write(self.style.WARNING(f"OK: {login}"))
            else:
                self.stdout.write(self.style.ERROR(f"Nenájdené medzi autormi: {login}"))
