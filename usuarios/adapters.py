from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email, user_field
from django.conf import settings
from django.urls import reverse
from django.contrib import messages
from .models import User

class CustomAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return settings.OPEN_FOR_SIGNUP or False
    
    def get_login_redirect_url(self, request):
        """
        Redireciona o usuário para o dashboard apropriado baseado no seu perfil
        """
        user = request.user
        if user.is_authenticated:
            if user.is_superuser or user.perfil == 'administrador':
                return reverse('admin_dashboard')
            elif user.perfil == 'monitor':
                return reverse('monitor_dashboard')
            else:
                return reverse('index')
        return super().get_login_redirect_url(request)


class SuapSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """Antes do login social, atualiza os dados do SUAP"""
        try:
            user = sociallogin.user
            extra_data = sociallogin.account.extra_data
            
            if extra_data:
                user.suap_id = extra_data.get('identificacao', '')
                user.suap_nome_completo = extra_data.get('nome', '')
                user.suap_email = extra_data.get('email', '')
                user.suap_vinculo = extra_data.get('tipo_vinculo', '')
                
                matricula = extra_data.get('matricula', '')
                if matricula:
                    user.suap_foto_url = f"https://suap.ifrn.edu.br/media/alunos/{matricula.upper()}.jpg"
                    print(f"SUAP Foto URL gerada: {user.suap_foto_url}")
                
                
                if not user.first_name and user.suap_nome_completo:
                    names = user.suap_nome_completo.split(' ', 1)
                    user.first_name = names[0]
                    if len(names) > 1:
                        user.last_name = names[1]
                
                if not user.email and user.suap_email:
                    user.email = user.suap_email
                    
        except Exception as e:
            print(f"Erro no pre_social_login: {e}")

    def save_user(self, request, sociallogin, form=None):
        """Salva o usuário após o login social"""
        user = super().save_user(request, sociallogin, form)
        
        try:
            extra_data = sociallogin.account.extra_data
            if extra_data:
                
                user.suap_id = extra_data.get('identificacao', '')
                user.suap_nome_completo = extra_data.get('nome', '')
                user.suap_email = extra_data.get('email', '')
                user.suap_vinculo = extra_data.get('tipo_vinculo', '')
                
                matricula = extra_data.get('matricula', '')
                if matricula:
                    user.suap_foto_url = f"https://suap.ifrn.edu.br/media/alunos/{matricula.upper()}.jpg"
                    print(f"SUAP Foto URL salva: {user.suap_foto_url}")
                
                user.save()
                print(f"Usuário {user.username} salvo com foto SUAP: {user.suap_foto_url}")
                
        except Exception as e:
            print(f"Erro no save_user: {e}")
        
        return user