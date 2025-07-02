from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    matricula = models.CharField(max_length=20, blank=True, null=True)
    perfil = models.CharField(max_length=20, choices=[('aluno', 'Aluno'), ('administrador', 'Administrador'), ('monitor', 'Monitor')], default='aluno')
    foto_perfil = models.ImageField(upload_to='perfil_fotos/', blank=True, null=True)
    def vinculo(self):
        if self.perfil == 'administrador' or self.is_superuser:
            return "Administrador"
        elif self.perfil == 'monitor':
            return "Monitor"
        return "Aluno"

    def __str__(self):
        return self.username