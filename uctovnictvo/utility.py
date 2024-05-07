# Rôzne utilitky nezávislé na modeloch
from ipdb import set_trace as trace
from PyPDF2 import PdfFileReader
import re

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import File

def NacitatUdajeFakturyTelekom(fdata):
    if type(fdata) == InMemoryUploadedFile: #ešte neuložený
        #fd = fdata
        return None
    else:
        fd=open(fdata.file.name, "rb")
    #fd=open(path, "rb")
    pdf = PdfFileReader(fd)
    pdftext = ""
    for nn in range(pdf.getNumPages()):
        page = pdf.getPage(nn)
        txt = page.extractText()
        pdftext += txt
    #Od 04/2024 faktúry nerozlišujú súčty podľa Hlas a Internet
    #do 03/2024
    mobilny_hlas = re.findall("Mobilný Hlas .* spolu ([0-9,]*)", pdftext)
    mobilny_internet = re.findall("Mobilný Internet .* spolu ([0-9,]*)", pdftext)
    #do 03/2024, snáď aj neskôr
    cislo_faktury = re.findall("FAKTÚRA č. (.*)",pdftext)[0]
    datum_splatnosti = re.findall("DÁTUM SPLATNOSTI ([0-9.]*)", pdftext)[0]
    ostatne_spolu = re.findall("OSTATNÉ SPOLU ([0-9,]*)", pdftext)
    ostatne_spolu = str(ostatne_spolu[0]) if ostatne_spolu else ""
    if ostatne_spolu:
        if float(ostatne_spolu.replace(",",".")) == 0.0:
                 ostatne_spolu = ""
    #od 04/2024
    if not mobilny_internet and not mobilny_hlas:
        #načítať po blokoch "Mobilné služby - číslo" ..... "Mobilné služby - číslo spolu" 
        mobilny_internet = []
        mobilny_hlas = []
        pdftext = pdftext.replace("\n", " ")
        sluzby = re.findall("Mobilné služby - [0-9]* .*? Mobilné služby - [0-9]* *spolu [0-9,]*", pdftext)
        for sluzba in sluzby:
            suma = re.findall("([0-9,]*)$", sluzba)[0] #suma je na konci
            if "internet" in sluzba: 
                mobilny_internet.append(suma)
            else:
                mobilny_hlas.append(suma)
    data = {
        "cislo_faktury": cislo_faktury,
        "mobilny_hlas": "+".join(mobilny_hlas),
        "mobilny_internet": "+".join(mobilny_internet),
        "ostatne_spolu": ostatne_spolu,
        "datum_splatnosti": datum_splatnosti
    }

    if type(fdata) == InMemoryUploadedFile:
        fdata.seek(0)
    else:
        fd.close()
    return data
