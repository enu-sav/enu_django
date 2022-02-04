from django.core.management import BaseCommand, CommandError
from django.utils import timezone
from django.contrib import messages
from ipdb import set_trace as trace
from uctovnictvo.models import DoVP, DoPC, StavDohody, AnoNie
from uctovnictvo.common import VytvoritSuborDohody

class Command(BaseCommand):
    help = 'Opraviť polia dohôd po zmene databázovej štruktúry vo februári 2022'

    def handle(self, *args, **kwargs):

        dohody = DoVP.objects.filter()
        for dohoda in dohody:
            changed=False
            if not dohoda.stav_dohody: 
                dohoda.stav_dohody = StavDohody.NOVA
                changed=True
            if not dohoda.vynimka:
                dohoda.vynimka = AnoNie.NIE
                changed=True
            status, msg, vytvoreny_subor = VytvoritSuborDohody(dohoda)
            if status != messages.ERROR:
                #necháme súbor, ktorý bol predtým
                #dohoda.subor_dohody = vytvoreny_subor
                if "2021" in dohoda.cislo:
                    dohoda.stav_dohody = StavDohody.PODPISANA_DOHODAROM
                else:
                    dohoda.stav_dohody = StavDohody.VYTVORENA
                changed=True
            if changed:
                dohoda.save()

        dohody = DoPC.objects.filter()
        for dohoda in dohody:
            changed=False
            if not dohoda.stav_dohody: 
                dohoda.stav_dohody = StavDohody.NOVA
                changed=True
            if not dohoda.vynimka:
                dohoda.vynimka = AnoNie.NIE
                changed=True
            status, msg, vytvoreny_subor = VytvoritSuborDohody(dohoda)
            if status != messages.ERROR:
                #necháme súbor, ktorý bol predtým
                #dohoda.subor_dohody = vytvoreny_subor
                dohoda.stav_dohody = StavDohody.VYTVORENA
                if "2021" in dohoda.cislo:
                    dohoda.stav_dohody = StavDohody.PODPISANA_DOHODAROM
                else:
                    dohoda.stav_dohody = StavDohody.VYTVORENA
                changed=True
            if changed:
                dohoda.save()

