from django import forms
from .models import Disponibilidade, Laboratorio

class DisponibilidadeForm(forms.ModelForm):
    class Meta:
        model = Disponibilidade
        fields = "__all__"

class LaboratorioForm(forms.ModelForm):
    class Meta:
        model = Laboratorio
        fields = "__all__"