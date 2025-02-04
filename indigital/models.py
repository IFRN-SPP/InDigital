from django.db import models
from usuarios.models import User

class Laboratorio(models.Model):
    numLaboratorio = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.numLaboratorio
    
class Reserva(models.Model):
    laboratorio = models.ForeignKey(Laboratorio, on_delete=models.CASCADE, null=True)
    horario = models.TimeField(blank=True, null=True)
    data = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.laboratorio