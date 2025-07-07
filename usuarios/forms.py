from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import BaseUserCreationForm
from .models import User

class CadastroForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ['matricula', 'username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(CadastroForm, self).__init__(*args, **kwargs)
        
        self.fields['matricula'].label = 'Matrícula'
        self.fields['username'].label = 'Nome'
        self.fields['email'].label = 'Email'
        self.fields['password1'].label = 'Senha'
        self.fields['password2'].label = 'Confirmar Senha'

        self.fields['matricula'].widget.attrs.update({'placeholder': 'Digite a sua matrícula'})
        self.fields['username'].widget.attrs.update({'placeholder': 'Digite o seu nome'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Digite o seu e-mail institucional'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Crie uma senha'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirme a senha'})

    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula')
        if User.objects.filter(matricula=matricula).exists():
            raise ValidationError("Já existe um usuário com esta matrícula.")
        return matricula

class EditarPerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'foto_perfil', 'perfil']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['username'].label = 'Nome'
        self.fields['email'].label = 'Email'
        self.fields['foto_perfil'].label = 'Foto de Perfil'