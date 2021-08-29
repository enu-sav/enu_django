from django.contrib import admin
from ipdb import set_trace as trace
from .models import EkonomickaKlasifikacia, Transakcia

#zobrazenie histórie
#https://django-simple-history.readthedocs.io/en/latest/admin.html
from simple_history.admin import SimpleHistoryAdmin

from import_export.admin import ImportExportModelAdmin


@admin.register(EkonomickaKlasifikacia)
class EkonomickaKlasifikaciaAdmin(SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("kod", "nazov")
    search_fields = ("^kod", "nazov")
    pass

@admin.register(Transakcia)
class TransakciaAdmin(SimpleHistoryAdmin, ImportExportModelAdmin):
    list_display = ("zdroj", "program", "zakazka", "ekoklas")
    #search_fields = ("zdroj", "program", "zakazka", "ekoklas")
    search_fields = ["^ekoklas__kod"]
    pass
