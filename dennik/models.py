from django.db import models
from beliana import settings
from simple_history.models import HistoricalRecords
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from uctovnictvo.models import Zdroj, TypZakazky, EkonomickaKlasifikacia, AnoNie
from uctovnictvo.storage import OverwriteStorage
from ipdb import set_trace as trace
import re, os

class InOut(models.TextChoices):
    PRIJATY = 'prijaty', 'Príjem'
    ODOSLANY = 'odoslany', 'Odoslanie'

class TypDokumentu(models.TextChoices):
    AZMLUVA = 'autorskazmluva', 'Autorská zmluva'
    VZMLUVA = 'vytvarnazmluva', 'Výtvarná zmluva'
    VOBJEDNAVKA = 'vobjednavka', 'Výtvarná objednávka'
    OBJEDNAVKA = 'objednavka', 'Objednávka'
    FAKTURA = 'faktura', 'Prijatá faktúra'
    VYSTAVENAFAKTURA = 'vystavenafaktura', 'Vystavená faktúra'
    PPLATBA = 'pplatba', 'Pravidelná platba'
    PSTRAVNE = 'pstravne', 'Príspevok na stravné'
    ZMLUVA = 'zmluva', 'Zmluva'
    DoVP = 'dovp', 'DoVP'
    DoPC = 'dopc', 'DoPC'
    DoBPS = 'dobps', 'DoBPS'
    HROMADNY = 'hromadny', 'Hromadný dokument'
    VYPLACANIE_AH = 'vyplacanie_ah', 'Vyplácanie autorských honorárov'
    VYPLACANIE_VH = 'vyplacanie_vh', 'Vyplácanie výtvarných honorárov'
    NAJOMNE = 'najomne', 'Nájomné'
    PRAVIDELNAPLATBA = 'pravidelnaplatba', 'Pravidelná platba'
    INTERNYPREVOD = 'internyprevod', 'Interný prevod'
    POKLADNICNAKNIHA = 'pokladnicnakniha', 'Pokladničná kniha'
    REKREACIA = 'rekreacia', 'Príspevok na rekreáciu'
    DOKUMENT = 'posta', 'Pošta'
    NEPRITOMNOST = 'nepritomnost', 'Neprítomnosť'
    ODMENA_OPRAVA = 'odmena_oprava', 'Odmena/Oprava'
    DROBNY_NAKUP = 'drobny_nákup', 'Drobný nákup'
    INY = 'iny', 'Iný'

class TypListu(models.TextChoices):
    DOPORUCENE = 'doporucene', 'Doporučene'
    OBYCAJNE = 'obycajne', 'Obyčajne'

# Typy šablón na vyplňovanie. Určuje, zoznam povolených tokenov v šablóne
class TypFormulara(models.TextChoices):
    VSEOBECNY = 'vseobecny', 'Všeobecný dokument'    #Ľubovoľné tokeny, bez väzby na databázu
    #AUTOR = 'autor', 'Formulár k autorským zmluvám'    #Ľubovoľné tokeny plus vybrané tokeny autorských zmlúv
    #DOHZAM = 'dohzam', 'Formulár pre dohodárov a zamestnancov'    #Ľubovoľné tokeny plus vybrané tokeny pre dohodárov a zamestnancov
    AH_ZRAZENA = 'ah_zrazena', 'Potvrdenie o zrazení dane z autorských honorárov'    # bez dátového súboru

class SposobDorucenia(models.TextChoices):
    POSTA = 'posta', 'Pošta'
    IPOSTA = 'iposta', 'Interná pošta'
    IPOSTAMAIL = 'ipostamail', 'Interná pošta + E-mail'
    OBLAKMAIL = 'oblakmail', 'Na oblak CVČ + E-mail'
    OBLAK = 'oblak', 'Na oblak CVČ'
    MAIL = 'mail', 'E-mail'
    OSOBNE = 'osobne', 'Osobne'
    WEB = 'web', 'Web rozhranie'

# Create your models here.
def dennik_file_path(instance, filename):
    return os.path.join(settings.DENNIK_DIR_NAME, filename)
class Dokument(models.Model):
    oznacenie = "D"    #v čísle dokument, D-2021-123
    cislo = models.CharField("Číslo", max_length=50)
    zrusene = models.CharField("Zrušené", 
            help_text = "Zvoľté 'Áno', ak záznam treba označit ako zrušený. V tom prípade v poli 'Poznámka' uveďte príčinu",
            max_length=10, 
            null=True, 
            choices=AnoNie.choices,
            default=AnoNie.NIE)
    poznamka = models.CharField("Poznámka", 
            help_text = "Poznámka. Povinné len v prípade, ak ide o zrušenie záznamu.",
            max_length=60,
            blank = True,
            null=True
            )
    cislopolozky = models.CharField("Súvisiaca položka", 
            null = True,
            help_text = """Ak je to relevantné, uveďte číslo súvisiacej položky v Djangu (zmluvy, dohody), inak vložte pomlčku '-'.<br />
            V prípade 
            <ul>
            <li>  ‣  <strong>prijatej faktúry</strong> najskôr vytvorte novú prijatú faktúru a</li>
            <li>  ‣  <strong>prijatej podpísanej autorskej zmluvy</strong> od autora najskôr vrátenie zaznamenajte v poli <em>Vrátená
podpísaná</em> v zmluve</li>
            </ol>
            a následne len upravte záznam pošty, ktorý sa tým vytvorí.<br />
            V prípade <strong>odosielaných dokumentov</strong>, ktoré sa vytvárajú v Djangu, už pre ne môže v tomto denníku existovať záznam. Skontrolujte to, a ak záznam existuje, použite ten.""", 
            max_length=200)
    typdokumentu = models.CharField("Typ dokumentu",
            max_length=20, choices=TypDokumentu.choices, 
            help_text = "Uveďte typ dokumentu. <strong>Netreba vypĺňať, ak je v poli <em>Súvisiaca položka</em> uvedená položka databázy v tvare X-RRRR-NNN</strong>, napr. <em>DoVP-2021-001</em>.",
            blank = True,
            null=True)
    adresat = models.CharField("Odosielateľ / Adresát", 
            help_text = "Uveďte adresáta. <br /><strong>Netreba vypĺňať, ak je v poli Súvisiaca položka uvedená položka databázy v tvare X-RRRR-NNN</strong>, napr. <em>DoVP-2021-001</em>.",
            blank = True,
            max_length=200)
    inout = models.CharField("Príjem / odoslanie",
            max_length=20, choices=InOut.choices, null=True)
    datum = models.DateField('Dátum príjmu / odoslania',
            help_text = "Dátum príjmu / odoslania dokumentu",
            null = True,
            )
    #odosielatel not used
    #odosielatel = models.CharField("xTyp dokumentu", 
            #max_length=200,
            #blank = True)
    #url not used
    #url = models.URLField('URL', 
            #help_text = "Zadajte URL.",
            #blank = True)
    sposob = models.CharField("Spôsob doručenia",
            help_text = "Zvoľte spôsob, akým bol dokument prijatý/doručený",
            max_length=20, choices=SposobDorucenia.choices, null=True)
    vec = models.CharField("Popis", 
            help_text = "Stručne popíšte obsah, napr. 'Podpísaná zmluva'. Ak je pole predvyplnené, netreba ho meniť.",
            max_length=200)
    naspracovanie = models.CharField("Na spracovanie", 
            help_text = "<strong>Ak ide o prijatý dokument</strong>, uveďte meno osoby, ktorej bol daný na vybavenie. Pri odosielanom dokumente vypĺňať netreba.",
            max_length=50,
            blank = True,
            null = True)
    suborposta = models.FileField("Súbor s poštou",
            help_text = "Vložte súbor s prijatou / odoslanou poštou (ak nebola súčasťou inej položky)",
            storage=OverwriteStorage(), 
            upload_to=dennik_file_path, 
            null = True, 
            blank = True 
            )
    #pozor: prehodené popisy polí prijalodoslal a zaznamvytvoril
    prijalodoslal = models.CharField("Záznam vytvoril", 
            help_text = "Meno používateľa, ktorý záznam v denníku vytvoril (vypĺňané automaticky)",
            max_length=50,
            blank = True)
    zaznamvytvoril = models.CharField("Prijal/odoslal", 
            help_text = "Meno používateľa, ktorý zaznamenal prijatie / odoslanie zásielky (vypĺňané automaticky).",
            max_length=50,
            blank = True)
    datumvytvorenia = models.DateField("Dátum vytvorenia záznamu",
            help_text = "Dátum vytvorenia záznamu (vypĺňané automaticky)",
            null = True)

    def clean(self):
        if self.zrusene == AnoNie.ANO and not self.poznamka:
            raise ValidationError({'poznamka':"V prípade zrušenia záznamu v poli 'Poznámka' uveďte príčinu"})
        elif self.zrusene == AnoNie.ANO:
            self.inout=None
            self.datum=None
            self.sposob=None

    def adresat_text(self):
        return self.adresat

    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Prijatá alebo odoslaná pošta'
        verbose_name_plural = 'Denník prijatej a odoslanej pošty'
    def __str__(self):
        return(self.cislo)

def form_file_path(instance, filename):
    return os.path.join(settings.FORM_DIR_NAME, filename)
# používaný názov Hromadný dokument
class Formular(models.Model):
    oznacenie = "HD"
    cislo = models.CharField("Číslo", max_length=50, null=True)
    typformulara = models.CharField("Typ šablóny",
            max_length=20, choices=TypFormulara.choices, 
            help_text = f"""Uveďte typ šablóny. Určuje, aké tokeny možno použiť:
                <ul>
                <li style="list-style-type:square"><em>{TypFormulara.VSEOBECNY.label}</em>: ľubovoľné tokeny, bez väzby na databázu</li>
                <li style="list-style-type:square"><em>{TypFormulara.AH_ZRAZENA.label}</em>: v dátovom súbore zadajte len stĺpec 'za_rok' s jedným riadkom, v ktorom je uvedený rok, za ktorý sa má potvrdenie vytvoriť.<br />Povolené tokeny:</li>
                <li style="list-style-type:square"> Ako dátum vytvorenia dokumentu možno použiť token <em>dat_vytv</em>. Ak sa v dátovom súbore neuvedie, vloží sa aktuálny dátum.</li>
                </ul>""",
            null=True)
    subor_nazov =  models.CharField("Názov",
            help_text = "Krátky názov dokumentu (použije sa ako názov vytvorených súborov)",
            max_length=40)
    subor_popis = models.TextField("Popis",
            help_text = "Dlhší popis k dokumentu: účel, poznámky a pod.",
            blank = True,
            max_length=600)
    typlistu = models.CharField("Typ listu", 
            help_text = "Zvoľté typ listu",
            max_length=10, 
            null=True, 
            choices=TypListu.choices
            )
    triedalistu = models.IntegerField("Trieda",
            help_text = "Uveďte triedu listu (1 alebo 2)",
            null = True
            )
    na_odoslanie = models.DateField('Na odoslanie dňa',
            help_text = 'Zadajte dátum odovzdania vytvorených dokumentov na sekretariát na odoslanie. <br />Vytvorí sa záznam v <a href="/admin/dennik/dokument/">denníku prijatej a odoslanej pošty</a>.</br />Po odoslaní nemožno ďalej upravovať',
            blank=True, null=True)
    # opakované uploadovanie súboru vytvorí novú verziu
    #subor = models.FileField("Súbor",upload_to=TMPLTS_DIR_NAME, null = True, blank = True)
    # opakované uploadovanie súboru prepíše existujúci súbor (nevytvorí novú verziu)
    #fodt súbor šablóny
    sablona = models.FileField("Šablóna dokumentu", storage=OverwriteStorage(),
            help_text = "FODT súbor šablóny na generovanie dokumentu. <br />Polia na vyplnenie musia byť definované ako [[tokeny]] s dvojitými hranatými zátvorkami.<br />Za posledným riadkom strany musí byť vložené <em>zalomenie strany</em>.<br />Tokeny sa musia presne zhodovať s názvami stĺpcov v dátovom súbore.",
            upload_to=form_file_path,
            validators=[FileExtensionValidator(allowed_extensions=['fodt'])],
            null = True,
    )
    #xlsx súbor s dátami na vyplnenie šablóny
    data = models.FileField("Dáta", storage=OverwriteStorage(),
            help_text = "XLSX súbor s dátami na generovanie. <br />Názvy stĺpcov sa musia presne zhodovať s tokenmi v šablóne (bez zátvoriek).<br />Názvy stĺpcov, ktoré majú byť formátované s dvomi desatinnými miestami, musia začínať 'n_'.",
            upload_to=form_file_path,
            validators=[FileExtensionValidator(allowed_extensions=['xlsx'])],
            null = True
    )
    #vytvorený hromadný dokument
    vyplnene = models.FileField("Vytvorený súbor", storage=OverwriteStorage(),
            help_text = "Vytvorený súbor hromadného dokumentu vo formáte FODT (vytvorený akciou 'Vytvoriť súbor hromadného dokumentu').",
            upload_to=form_file_path,
            blank=True,
            null = True
    )
    #dáta použité na vytvorenie hromadného dokumentu
    vyplnene_data = models.FileField("Vyplnené dáta", storage=OverwriteStorage(),
            help_text = "Vytvorený XLSX súbor s dátami použitými na vytvorenie hromadného dokumentu (vytvorený akciou 'Vyplniť formulár').",
            upload_to=form_file_path,
            blank=True,
            null = True
    )
    #Podací hárok
    podaciharok = models.FileField("Podací hárok", storage=OverwriteStorage(),
            help_text = "Vytvorený podací hárok pre Slovenskú poštu. Pred použitím na stránke pošty ho treba <strong>skonvertovať do formátu XLS</strong>",
            upload_to=form_file_path,
            blank=True,
            null = True
    )
    #Finálny hromadný dokument. Ak bol hromadný dokument rozdelený, priložiť zip archív
    rozposlany = models.FileField("Rozposlaný dokument", storage=OverwriteStorage(),
            help_text = "Pdf vytlačeného a rozposlaného dokumentu. Ak bol hromadný dokument rozdelený, priložiť zip archív so všetkými pdf súbormi.",
            validators=[FileExtensionValidator(allowed_extensions=['pdf', 'zip'])],
            upload_to=form_file_path,
            blank=True,
            null = True
    )
    #dáta použité na vytvorenie hromadného dokumentu s komentárom
    data_komentar = models.FileField("Upravené vyplnené dáta", storage=OverwriteStorage(),
            help_text = "Upravený XLSX súbor z poľa 'Vyplnené dáta' s prípadnými zmenami, ktoré boli ručne spravené v rozposlanom dokumente a komentárom.",
            upload_to=form_file_path,
            validators=[FileExtensionValidator(allowed_extensions=['xlsx'])],
            blank=True,
            null = True
    )

    def clean(self): 
        if self.triedalistu not in (1, 2):
            raise ValidationError({'triedalistu':"Povolené hodnoty triedy listu sú len 1 a 2."})
    history = HistoricalRecords()
    class Meta:
            verbose_name = 'Hromadný dokument'
            verbose_name_plural = 'Hromadné dokumenty'
    def __str__(self):
            return(self.subor_nazov)
 
class CerpanieRozpoctu(models.Model):
    # unikátny identifikátor na rozlíšenie sumy podľa klasifikácie a dátumu
    unikatny =  models.CharField("Unikátny identifikátor",
            max_length=80,
            blank = True,
            null = True
    )
    polozka =  models.CharField("Položka",
            max_length=80,
            null = True
    )
    mesiac = models.DateField('Mesiac',
            null = True,
            blank = True,
            )
    suma = models.DecimalField("Suma v EUR", 
            max_digits=8, 
            decimal_places=2, 
            null=True,
            blank=True)

    zdroj = models.ForeignKey(Zdroj,
            on_delete=models.PROTECT,
            related_name='%(class)s_klasifikacia',
            null=True,
            blank=True)
    zakazka = models.ForeignKey(TypZakazky,
            on_delete=models.PROTECT,
            verbose_name = "Typ zákazky",
            related_name='%(class)s_klasifikacia',
            null=True,
            blank=True)
    ekoklas = models.ForeignKey(EkonomickaKlasifikacia,
            on_delete=models.PROTECT,
            verbose_name = "Ekonomická klasifikácia",
            related_name='%(class)s_klasifikacia',
            null=True,
            blank=True)

    class Meta:
            verbose_name = 'Čerpanie rozpočtu'
            verbose_name_plural = 'Čerpanie rozpočtu'
    def __str__(self):
            return(f"{self.polozka}-{self.mesiac}")


def pr_file_path(instance, filename):
    return os.path.join(settings.PLATOVA_REKAPITULACIA_DIR_NAME, filename)
class PlatovaRekapitulacia(models.Model):
    identifikator = models.CharField("Identifikátor",
            help_text = "Identifikátor v tvare RRRR-MM. Doplní sa automaticky, ak názov súboru obsahuje údaje o období.",
            max_length=50,
            null=True,
            blank=True)
    subor = models.FileField("Súbor s platovou rekapituláciou",
            help_text = "Vložte súbor s platovou rekapituláciou.<br />Ak názov obsahuje údaje o období v tvare MM.RRRR alebo RRRR.MM (na mieste . môže byť hocijaký znak), tak sa automaticky vyplní pole Identifikátor.",
            storage=OverwriteStorage(), 
            upload_to=pr_file_path
            )
    rozdiel_minus = models.DecimalField("Max. záporný rozdiel",
            help_text = "Vypočíta sa akciou 'Porovnať mzdové údaje s platovou rekapituláciou'",
            max_digits=8, 
            decimal_places=2, 
            null=True,
            blank=True)
    rozdiel_plus = models.DecimalField("Max. kladný rozdiel",
            help_text = "Vypočíta sa akciou 'Porovnať mzdové údaje s platovou rekapituláciou'",
            max_digits=8, 
            decimal_places=2, 
            null=True,
            blank=True)

    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Platová rekapitulácia'
        verbose_name_plural = 'Platová rekapitulácia'
    def __str__(self):
        return(self.identifikator)

    def clean(self): 
        rslt=re.findall(r"([0-9][0-9]).?(202[0-9])",self.subor.name)
        if rslt:
            mesiac,rok = rslt[0]
        if not rslt:
            rslt=re.findall(r"(202[0-9]).?([0-9][0-9])",self.subor.name)
            if rslt:
                rok,mesiac = rslt[0]
        if not rslt:
            raise ValidationError(f"Názov súboru {self.subor.name} neobsahuje údaje o období v tvare MMRRRR, MM-RRRR, RRRRMM ani RRRR-MM. Vyplňte pole Identifikátor alebo vložte iný (správny) súbor.")
        rslt = rslt[0]
        self.identifikator = f"{rslt[1]}-{rslt[0]}"
        pass


def system_file_path(instance, filename):
    return os.path.join(settings.TMPLTS_DIR_NAME, filename)

class SystemovySubor(models.Model):
    subor_nazov =  models.CharField("Názov", max_length=100)
    subor_popis = models.TextField("Popis/účel", max_length=250)
    # opakované uploadovanie súboru vytvorí novú verziu
    #subor = models.FileField("Súbor",upload_to=TMPLTS_DIR_NAME, null = True, blank = True)
    # opakované uploadovanie súboru prepíše existujúci súbor (nevytvorí novú verziu)
    subor = models.FileField(storage=OverwriteStorage(), upload_to=system_file_path, null = True, blank = True)
    history = HistoricalRecords()
    class Meta:
        verbose_name = 'Systémový súbor'
        verbose_name_plural = 'Systémové súbory'
    def __str__(self):
        return(self.subor_nazov)

