from django.db import models

class Laboratorio(models.Model):
    numLaboratorio = models.TextField(max_length=30)
    horario = models.TimeField()

class Reserva(models.Model):
    data = models.DateField()
    laboratorio = models.ForeignKey(Laboratorio, on_delete=models.CASCADE)