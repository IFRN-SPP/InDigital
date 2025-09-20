from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email, user_field
from django.conf import settings
from django.urls import reverse


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
            else:  # perfil == 'aluno' ou qualquer outro
                return reverse('index')
        return super().get_login_redirect_url(request)


class SuapSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        # Extra data in: sociallogin.account.extra_data
        user = sociallogin.user
        user_email(user, data.get("email") or "")
        user_field(user, "first_name", data.get("first_name"))
        user_field(user, "last_name", data.get("last_name"))
        user_field(user, "username", data.get("username"))
        return user

    def is_open_for_signup(self, request, sociallogin):
        return settings.OPEN_FOR_SIGNUP or False