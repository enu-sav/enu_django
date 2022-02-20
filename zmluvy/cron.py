from django.core.mail import send_mail
from .models import PlatbaAutorskaSumar
from ipdb import set_trace as trace
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from beliana.settings import SITE_HOST, SITE_URL
from django.core.mail import send_mail
from django.contrib.auth.models import User

# notifikácie kvôli finančnému úradu
def notifikacie_FU():
    #načítať všetky doposiaľ neoznámené platby
    neoznamene = PlatbaAutorskaSumar.objects.filter(datum_oznamenia__isnull=True, datum_uhradenia__isnull=False)
    spravy=[]
    for platba in neoznamene:
        #určiť počet dní do termínu
        du = platba.datum_uhradenia
        termin = date(du.year, du.month,15)+relativedelta(months=1)
        zostava = (termin - date.today()).days
        #http://samba.enu.sav.sk:8000/admin/zmluvy/platbaautorskasumar/14/change/
        mmm = f'Platbu {platba.cislo} ({SITE_URL}admin/zmluvy/platbaautorskasumar/{platba.id}/change) treba na finančný úrad oznámiť do {termin.strftime("%d. %m. %Y")}.'
        if (termin - date.today()) == timedelta(days=12):
            spravy.append(f"{mmm} Zostáva {zostava} dní.")
        elif (termin - date.today()) == timedelta(days=5):
            spravy.append(f"{mmm} Zostáva {zostava} dní.")
        elif (termin - date.today()) == timedelta(days=1):
            spravy.append(f"{mmm} Zostáva 1 deň.")
        elif (termin - date.today()) < timedelta(days=1):
            spravy.append = f"Platbu {platba.cislo} treba na finančný úrad oznámiť ihneď."
        elif (termin - date.today()) < timedelta(days=3):
            spravy.append(f"{mmm} Zostávajú {zostava} dni.")

    message = "Termíny oznámenia finančnej správe:"
    for sprava in spravy:
        message = f"{message}\n{sprava}"

    #Používatelia s príslušným oprávnením
    users = User.object.all()


    #Nedokončené, treba vybrať používateľov s právom pas_notif_fs 
    #rslt = send_mail('Termíny oznámenia finančnej správe', message, "django-noreply@enu.savba.sk", ["sramek.milos@gmail.com"])
    trace()
    pass
