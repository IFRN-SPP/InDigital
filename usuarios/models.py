from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    matricula = models.CharField(max_length=20, blank=True, null=True)
    turno = models.CharField(max_length=20, choices=[('matutino', 'Matutino'), ('vespertino', 'Vespertino'), ('noturno', 'Noturno')], blank=True)
    serie = models.CharField(max_length=10, blank=True)
    
    def __str__(self):
        return self.username