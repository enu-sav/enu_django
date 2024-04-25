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
    mobilny_hlas = re.findall("Mobilný Hlas .* spolu ([0-9,]*)", pdftext)
    mobilny_internet = re.findall("Mobilný Internet .* spolu ([0-9,]*)", pdftext)
    ostatne_spolu = re.findall("OSTATNÉ SPOLU ([0-9,]*)", pdftext)
    ostatne_spolu = str(ostatne_spolu[0]) if ostatne_spolu else ""
    data = {
            "cislo_faktury": re.findall("FAKTÚRA č. (.*)",pdftext)[0],
            "mobilny_hlas": "+".join(mobilny_hlas),
            "mobilny_internet": "+".join(mobilny_internet),
            "ostatne_spolu": ostatne_spolu,
            "datum_splatnosti": re.findall("DÁTUM SPLATNOSTI ([0-9.]*)", pdftext)[0]
            }

    if type(fdata) == InMemoryUploadedFile:
        fdata.seek(0)
    else:
        fd.close()
    return data
