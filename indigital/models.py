from django.db import models
from usuarios.models import User
from django.core.exceptions import ValidationError

class Laboratorio(models.Model):
    num_laboratorio = models.CharField(max_length=10, unique=True)
    capacidade = models.IntegerField(default=30)

    def __str__(self):
        return self.num_laboratorio
    
class Disponibilidade(models.Model):
    laboratorio = models.ForeignKey(Laboratorio, on_delete=models.CASCADE)
    horario_inicio = models.TimeField()
    horario_fim = models.TimeField()
    data = models.DateField()
    vagas = models.IntegerField()
    monitor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monitor_disponibilidade', null=True, blank=True)

    class Meta:
        unique_together = ('laboratorio', 'data', 'horario_inicio', 'horario_fim')

    def clean(self):
        super().clean()
        if self.vagas < 1:
            raise ValidationError("O número de vagas deve ser no mínimo 1.")

        if self.vagas > self.laboratorio.capacidade:
            raise ValidationError("O número de vagas não pode ser maior que a capacidade do laboratório.")

    def __str__(self):
        return self.laboratorio.num_laboratorio
    
class Reserva(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    disponibilidade = models.ForeignKey(Disponibilidade, on_delete=models.CASCADE)

    status_frequencia = models.CharField(max_length=1, choices=[('P', 'Presente'), ('F', 'Faltou')], default='', blank=True)

    def __str__(self):
        return self.usuario.username
    
class FilaEspera(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    disponibilidade = models.ForeignKey(Disponibilidade, on_delete=models.CASCADE)
    data_solicitacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'disponibilidade')
        ordering = ['data_solicitacao']