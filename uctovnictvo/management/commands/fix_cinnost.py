from django.core.management import BaseCommand, CommandError
from django.utils import timezone
from django.contrib import messages
from ipdb import set_trace as trace
from uctovnictvo.models import PrijataFaktura, Cinnost, PravidelnaPlatba, PrispevokNaStravne, PlatovyVymer
from uctovnictvo.models import DoPC, DoVP, DoBPS, NajomneFaktura

class Command(BaseCommand):
    help = 'Opraviť Činnosť - zavedená v r. 2022'

    def handle(self, *args, **kwargs):

        c_nic=Cinnost.objects.filter(kod="-")[0]
        c_1a=Cinnost.objects.filter(kod="1a")[0]

        typy = [PrijataFaktura, PravidelnaPlatba, NajomneFaktura, PrispevokNaStravne, DoBPS, DoVP, DoPC]
        for typ in typy:
            items = typ.objects.filter()
            for item in items:
                if "2021" in item.cislo:
                    print(item.cislo, c_nic)
                    item.cinnost=c_nic
                    item.save()
                elif "2022" in item.cislo:
                    print(item.cislo, c_1a)
                    item.cinnost=c_1a
                    item.save()
                else:
                    print(item.cislo)
                pass

        vymery = PlatovyVymer.objects.filter()
        for vymer in vymery:
            print(vymer.zamestnanec)
            vymer.cinnost=c_nic
            vymer.save()

