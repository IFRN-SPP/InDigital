from django.contrib import admin
from .models import Laboratorio, Reserva, Disponibilidade

admin.site.register(Reserva)
admin.site.register(Laboratorio)
admin.site.register(Disponibilidade)