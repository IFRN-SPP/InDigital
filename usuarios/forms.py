from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import BaseUserCreationForm
from .models import User

class CadastroForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(CadastroForm, self).__init__(*args, **kwargs)
        
        self.fields['username'].label = 'Matrícula'
        self.fields['first_name'].label = 'Primeiro Nome'
        self.fields['last_name'].label = 'Sobrenome'
        self.fields['email'].label = 'Email'
        self.fields['password1'].label = 'Senha'
        self.fields['password2'].label = 'Confirmar Senha'

        self.fields['username'].widget.attrs.update({'placeholder': 'Digite a sua matrícula'})
        self.fields['first_name'].widget.attrs.update({'placeholder': 'Digite o seu primeiro nome'})
        self.fields['last_name'].widget.attrs.update({'placeholder': 'Digite o seu sobrenome'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Digite o seu e-mail institucional'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Crie uma senha'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirme a senha'})

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Já existe um usuário com esta matrícula.")
        return username

class EditarPerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'foto_perfil', 'perfil']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['first_name'].label = 'Primeiro Nome'
        self.fields['last_name'].label = 'Sobrenome'
        self.fields['email'].label = 'Email'
        self.fields['foto_perfil'].label = 'Foto de Perfil'
        self.fields['perfil'].label = 'Perfil'

from allauth.account.forms import (
    LoginForm,
    ResetPasswordForm,
    ResetPasswordKeyForm,
)
class UserLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})


class UserResetPasswordForm(ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})


class UserResetPasswordKeyForm(ResetPasswordKeyForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})