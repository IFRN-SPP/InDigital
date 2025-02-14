from django.db import models
from usuarios.models import User

class Laboratorio(models.Model):
    num_laboratorio = models.CharField(max_length=10, unique=True)
    vagas = models.IntegerField(default=30)

    def __str__(self):
        return f"{self.num_laboratorio} ({self.vagas})"
    
class Disponibilidade(models.Model):
    laboratorio = models.ForeignKey(Laboratorio, on_delete=models.CASCADE)
    horario = models.TimeField()
    data = models.DateField()

    def __str__(self):
        return self.laboratorio.num_laboratorio
    
class Reserva(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    disponibilidade = models.ForeignKey(Disponibilidade, on_delete=models.CASCADE)

    def __str__(self):
        return self.usuario.username