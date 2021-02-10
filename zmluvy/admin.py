from django.contrib import admin

# Register your models here.
from .models import Osoba, Zmluva

admin.site.register(Osoba)
admin.site.register(Zmluva)
