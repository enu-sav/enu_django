import csv
from django.core.management import BaseCommand, CommandError
from zmluvy.models import PlatbaAutorskaOdmena, PlatbaAutorskaSumar
from zmluvy.vyplatitautorske import VyplatitAutorskeOdmeny
from django.utils import timezone
import re, os
import logging

class Command(BaseCommand):
    help = 'Vygenerovať podklady na vyplácanie autorských odmien'
    WARNING, ERROR, SUCCESS = (1,2,3)

    def log(self, ltype, text):
        if ltype is self.WARNING:
            self.stdout.write(self.style.WARNING(text))
        elif ltype is self.ERROR:
            self.stdout.write(self.style.ERROR(text))
        elif ltype is self.SUCCESS:
            self.stdout.write(self.style.SUCCESS(text))
        

    def add_arguments(self, parser):
        parser.add_argument('--na-vyplatenie', type=str, help=f"Priečinok s názvom RRRR-MM v {VyplatitAutorskeOdmeny.ah_cesta} so súbormi s údajmi pre vyplácanie autorských honorárov")
        parser.add_argument('--datum-vyplatenia', type=str, help="Dátum vyplatenia hesiel v tvare 'dd.mm.rrrr'. Zadať až po vyplatení hesiel THS-kou. Ak sa nezadá, vygenerujú sa len podklady pre THS-ku na vyplácanie. Ak sa zadá, aktualizuje sa databáza a vygenerujú sa zoznamy vyplatených hesiel na importovanie do RS a WEBRS, ako aj potvrdenie o zaplatení na zaradenie do šanonu.")
        parser.add_argument("--zrusit-platbu" , default=False ,help="Zrušiť všetky platby pre vyplácanie určené prepínačom --na-vyplatenie", dest='zrusit_platbu', action='store_true')
        parser.add_argument("--negenerovat-subory" , default=False ,help="aktualizuje sa databáza, ale súbory sa negenerujú", dest='negenerovat_subory', action='store_true')

    def handle(self, *args, **kwargs):
        if kwargs['na_vyplatenie']:
            za_mesiac = kwargs['na_vyplatenie']
        else:
            self.log(self.ERROR, f"Nebol zadaný názov priečinka v '{VyplatitAutorskeOdmeny.ah_cesta}' v tvare 'mm-rrrr' s údajmi na vyplatenie")

        self.negenerovat_subory = kwargs['negenerovat_subory']

        self.db_logger = logging.getLogger('db')
        if kwargs['zrusit_platbu']:
            platby = PlatbaAutorskaOdmena.objects.filter(obdobie=za_mesiac)
            if platby:
                ao = VyplatitAutorskeOdmeny(self.db_logger, self.mylog)
                ao.zrusit_vyplacanie(za_mesiac)
            else:
                self.log(self.ERROR, f"Platby pre obdobie {za_mesiac} v databáze existujú, nemám čo zrušiť.")
        else:
            platby = PlatbaAutorskaOdmena.objects.filter(obdobie=za_mesiac)
            if platby:
                self.log(self.ERROR, f"Platby pre obdobie {za_mesiac} už v databáze existujú. Ak chcete operáciu vykonať, najskôr ich odstráňte pomocou prepínača --zrusit-platbu.")


            ao = VyplatitAutorskeOdmeny(settings.ROYALTIES_DIR, self.db_logger, self.mylog)
            ao.vyplatit_odmeny(za_mesiac, kwargs['datum_vyplatenia'])
            if  kwargs['datum_vyplatenia']:
                PlatbaAutorskaSumar.objects.create(
                    obdobie = za_mesiac,
                    #datum_uhradenia = kwargs['datum_vyplatenia']
                    datum_uhradenia = re.sub(r"([^.]*)[.]([^.]*)[.](.*)", r"\3-\2-\1", kwargs['datum_vyplatenia'])
                    ) 
    def mylog(self, status, msg):
        self.log(status, msg)
        if status == self.ERROR: raise SystemExit

