from allauth.account.signals import user_logged_in
from django.dispatch import receiver
from django.core.files.base import ContentFile
import requests

@receiver(user_logged_in)
def atualizar_dados_suap(sender, request, user, **kwargs):
    """Atualiza o usuário quando loga com SUAP."""
    social_account = user.socialaccount_set.filter(provider='suap').first()
    if not social_account:
        return

    extra_data = social_account.extra_data or {}

    user.suap_id = extra_data.get('identificacao')
    user.suap_nome_completo = extra_data.get('nome_usual') or extra_data.get('nome')
    user.suap_email = extra_data.get('email')
    user.suap_vinculo = extra_data.get('vinculo')
    user.suap_foto_url = extra_data.get('foto')

    # Baixa e salva a foto localmente, se existir
    if user.suap_foto_url and not user.foto_perfil:
        try:
            response = requests.get(user.suap_foto_url, timeout=5)
            if response.status_code == 200:
                user.foto_perfil.save(
                    f"{user.suap_id}_foto.jpg",
                    ContentFile(response.content),
                    save=False
                )
        except Exception as e:
            print(f"[ERRO] Não foi possível baixar a foto do SUAP: {e}")

    user.save()