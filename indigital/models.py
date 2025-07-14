from django.db import models
from usuarios.models import User

class Laboratorio(models.Model):
    num_laboratorio = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.num_laboratorio
    
class Disponibilidade(models.Model):
    laboratorio = models.ForeignKey(Laboratorio, on_delete=models.CASCADE)
    horario_inicio = models.TimeField()
    horario_fim = models.TimeField()
    data = models.DateField()
    vagas = models.IntegerField(default=30)

    class Meta:
        unique_together = ('laboratorio', 'data', 'horario_inicio', 'horario_fim')

    def __str__(self):
        return self.laboratorio.num_laboratorio
    
class Reserva(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    disponibilidade = models.ForeignKey(Disponibilidade, on_delete=models.CASCADE)

    frequencia = (
        ('P', 'Presente'),
        ('F', 'Faltou')
    )
    def __str__(self):
        return self.usuario.username
    
class FilaEspera(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    disponibilidade = models.ForeignKey(Disponibilidade, on_delete=models.CASCADE)
    data_solicitacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'disponibilidade')
        ordering = ['data_solicitacao']