from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import BaseUserCreationForm
from .models import User

class CadastroForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'matricula', 'turno', 'serie', 'foto_perfil', 'password1', 'password2']

class EditarPerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'matricula', 'foto_perfil']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.is_staff:
            self.fields['turno'] = forms.ChoiceField(
                choices=User._meta.get_field('turno').choices,
                required=False
            )
            self.fields['serie'] = forms.CharField(required=True, initial=self.instance.serie)