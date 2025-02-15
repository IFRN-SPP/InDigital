from django import forms
from .models import Disponibilidade, Laboratorio, Reserva

class DisponibilidadeForm(forms.ModelForm):
    class Meta:
        model = Disponibilidade
        fields = "__all__"

class LaboratorioForm(forms.ModelForm):
    class Meta:
        model = Laboratorio
        fields = "__all__"

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = "__all__"