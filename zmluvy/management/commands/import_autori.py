import csv
from django.core.management import BaseCommand, CommandError
from zmluvy.models import OsobaAutor
from ipdb import set_trace as trace

# 1. a 2. stlpec: uid a login autorov v RS
# 3. stlpec: Autori uvedení ako autori hesiel
aa_name = "../../../data/aktivni_autori_2021-03-13.csv"
aa_name = "data/autori-marec_2021.csv"

class Command(BaseCommand):
    help = 'Načítať používateľov exportovaných z redakčného systému (role Autor, Konzultant a Garant)'

    def read_aa(self):
        self.logins = {}
        self.aktivni_autori = []
        with open(aa_name, 'rt') as f:
            reader = csv.reader(f, dialect='excel')
            for row in reader:
                if row[0] == "Uid": continue
                self.logins[row[1]] = row[0]
                # aktívni autori v stĺpci 2
                #if len(row) > 2 and row[2]:
                    #self.aktivni_autori.append(row[2])
                # všetci autori v rs
                self.aktivni_autori.append(row[1])

    def handle(self, *args, **kwargs):
        self.read_aa()
        trace()
        for login in self.logins:
            uid = self.logins[login]
            if login in self.aktivni_autori:
                o_query_set = OsobaAutor.objects.filter(rs_uid=uid)
                if not o_query_set:
                    OsobaAutor.objects.create(
                    rs_uid = uid,
                    rs_login = login,
                    )
                    self.stdout.write(self.style.SUCCESS(f"OK: {login}"))
