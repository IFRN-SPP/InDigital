from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    username = models.CharField(max_length=20, unique=True, verbose_name='Matrícula')
    perfil = models.CharField(max_length=20, choices=[('aluno', 'Aluno'), ('administrador', 'Administrador'), ('monitor', 'Monitor')], default='aluno')
    foto_perfil = models.ImageField(upload_to='perfil_fotos/', blank=True, null=True)
    
    # Campos para dados do SUAP
    suap_id = models.CharField(max_length=20, blank=True, null=True, verbose_name='ID SUAP')
    suap_foto_url = models.URLField(blank=True, null=True, verbose_name='URL da Foto no SUAP')
    suap_nome_completo = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nome completo no SUAP')
    suap_email = models.EmailField(blank=True, null=True, verbose_name='E-mail no SUAP')
    suap_vinculo = models.CharField(max_length=100, blank=True, null=True, verbose_name='Vínculo no SUAP')
    
    def vinculo(self):
        if self.perfil == 'administrador' or self.is_superuser:
            return "Administrador"
        elif self.perfil == 'monitor':
            return "Monitor"
        return "Aluno"
    
    def get_foto_perfil_url(self):
        if self.foto_perfil:
            return self.foto_perfil.url
        elif self.suap_foto_url:
            return self.suap_foto_url
        return "https://via.placeholder.com/120"
    
    def get_nome_completo(self):
        if self.suap_nome_completo:
            return self.suap_nome_completo
        return super().get_full_name()
    
    def __str__(self):
        return self.username
    
    