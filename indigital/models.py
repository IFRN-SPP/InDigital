from django.db import models
from usuarios.models import User

class Reserva(models.Model):
    numLaboratorio = models.CharField(max_length=10, blank=True)
    horario = models.TimeField(blank=True, null=True)
    data = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.numLaboratorio