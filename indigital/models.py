from django.db import models
from usuarios.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime

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

    def start_datetime(self):
        """Retorna o datetime (aware) do início da disponibilidade usando o timezone atual."""
        dt = datetime.combine(self.data, self.horario_inicio)
        if timezone.is_naive(dt):
            tz = timezone.get_current_timezone()
            dt = timezone.make_aware(dt, tz)
        return timezone.localtime(dt)

    def end_datetime(self):
        """Retorna o datetime (aware) do fim da disponibilidade usando o timezone atual."""
        dt = datetime.combine(self.data, self.horario_fim)
        if timezone.is_naive(dt):
            tz = timezone.get_current_timezone()
            dt = timezone.make_aware(dt, tz)
        return timezone.localtime(dt)

    def is_passada(self):
        """Retorna True se a disponibilidade já começou (horário de início menor que agora).

        Observação: consideramos que, se o horário de início for anterior ao tempo atual, a
        disponibilidade já passou e não deve mais aceitar reservas.
        """
        agora = timezone.localtime(timezone.now())
        inicio = self.start_datetime()
        return agora > inicio

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
    status_aprovacao = models.CharField(max_length=1, choices=[('P', 'Pendente'), ('A', 'Aprovada'), ('R', 'Rejeitada'), ('C', 'Cancelada')], default='')
    data_solicitacao = models.DateTimeField(auto_now_add=True)

    status_frequencia = models.CharField(max_length=1, choices=[('P', 'Presente'), ('F', 'Faltou'), ('N', 'Não registrado')], default='', blank=True)

    def clean(self):
        super().clean()
        
        reserva_duplicada = Reserva.objects.filter(
            usuario=self.usuario,
            disponibilidade=self.disponibilidade
        ).exclude(id=self.id).first()
        
        if reserva_duplicada:
            if reserva_duplicada.status_aprovacao in ['P', 'A']:
                status_texto = "pendente" if reserva_duplicada.status_aprovacao == 'P' else "aprovada"
                raise ValidationError(
                    f"Você já possui uma reserva {status_texto} para este mesmo horário."
                )
        
        reservas_conflitantes = Reserva.objects.filter(
            usuario=self.usuario,
            disponibilidade__data=self.disponibilidade.data,
            status_aprovacao__in=['P', 'A'] 
        ).exclude(id=self.id)
        
        for reserva in reservas_conflitantes:
            inicio_atual = self.disponibilidade.horario_inicio
            fim_atual = self.disponibilidade.horario_fim
            inicio_existente = reserva.disponibilidade.horario_inicio
            fim_existente = reserva.disponibilidade.horario_fim
            
            if inicio_atual < fim_existente and inicio_existente < fim_atual:
                status_texto = "pendente" if reserva.status_aprovacao == 'P' else "aprovada"
                raise ValidationError(
                    f"Você já possui uma reserva {status_texto} que se sobrepõe a este horário na mesma data."
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