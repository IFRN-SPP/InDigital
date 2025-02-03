from django.db import models
from usuarios.models import User

class Reserva(models.Model):
    numLaboratorio = models.CharField(max_length=10)
    horario = models.TimeField()
    data = models.DateField()

    def __str__(self):
        return self.numLaboratorio