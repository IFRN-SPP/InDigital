from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager

class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    perfil = models.CharField(max_length=20, choices=[('aluno', 'Aluno'), ('administrador', 'Administrador'), ('monitor', 'Monitor'), ('outro', 'Outro')], default='aluno')
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
        elif self.perfil == 'outro':
            return "Outro"
        return "Aluno"
    
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.first_name or self.email
    
    def get_foto_perfil_url(self):
        if self.foto_perfil:
            return self.foto_perfil.url
        elif self.suap_foto_url:
            # Decodificar &amp; para & na URL do SUAP
            import html
            return html.unescape(self.suap_foto_url)
        # URL de um ícone padrão usando FontAwesome
        return "https://via.placeholder.com/120/6c757d/ffffff?text=👤"
    
    def get_nome_completo(self):
        if self.suap_nome_completo:
            return self.suap_nome_completo
        return super().get_full_name()