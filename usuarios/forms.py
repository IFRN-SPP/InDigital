from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import BaseUserCreationForm
from .models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit

class CadastroForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'matricula', 'turno', 'serie', 'password1', 'password2']

    