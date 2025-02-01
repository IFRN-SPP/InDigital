from django.db import models
from usuarios.models import User

class Laboratorio(models.Model):
    numLaboratorio = models.TextField(max_length=30)
    horario = models.TimeField()

class Reserva(models.Model):
    data = models.DateField()
    horario = models.TimeField(null=True,blank=True)
    laboratorio = models.ForeignKey(Laboratorio, on_delete=models.CASCADE)