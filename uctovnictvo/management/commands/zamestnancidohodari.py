import csv, re
from django.core.management import BaseCommand, CommandError
from django.utils import timezone
from ipdb import set_trace as trace
from datetime import date
from simple_history.utils import update_change_reason

from uctovnictvo.models import ZamestnanecDohodar, Zamestnanec, Dohodar, DoVP, DoPC

class Command(BaseCommand):
    help = 'Načítať údaje o zamestnancoch a dohodaroch'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help="csv súbor s dátami o zamestnancoch a dohodároch")

    def read_data(self, path):
        hdr = []
        data ={}
        with open(path, 'rt') as f:
            reader = csv.reader(f, dialect='excel')
            for row in reader:
                if not hdr:
                    hdr = row[1:]
                    continue
                rrr = [r.replace("\xa0","") for r in row]
                data[rrr[0]] = rrr[1:]
        return hdr, data

    def handle(self, *args, **kwargs):
        path = kwargs['path']
        hdr, zamestnanci = self.read_data(path)
        nn={}
        for n, val in enumerate(hdr):
            nn[val]=n
        trace()
        zd_set = ZamestnanecDohodar.objects.filter()

        for zd in zd_set:
            if zd.priezvisko in zamestnanci:
                osoba = Zamestnanec()
            else:
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
                osoba.cislo_zamestnanca = zamestnanci[zd.priezvisko][0]
                osoba.zapocitane_roky = zamestnanci[zd.priezvisko][1]
                osoba.zapocitane_dni = zamestnanci[zd.priezvisko][2]
                dd, mm, rr =re.findall(r"([0-9]*)[.]([0-9]*)[.]([0-9]*)", zamestnanci[zd.priezvisko][3])[0]
                osoba.zamestnanie_od = date(int(rr),int(mm),int(dd)) 
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
            zd.delete()
        pass
