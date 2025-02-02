from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    matricula = models.CharField(max_length=20, unique=True)
    turno = models.CharField(max_length=20, choices=[('matutino', 'Matutino'), ('vespertino', 'Vespertino'), ('noturno', 'Noturno')])
    serie = models.CharField(max_length=10)
    
    def __str__(self):
        return self.username