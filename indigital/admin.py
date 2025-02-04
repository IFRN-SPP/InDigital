from django.contrib import admin
from .models import Laboratorio, Reserva

admin.site.register(Reserva)
admin.site.register(Laboratorio)