from django import forms
from .models import Laboratorio, Reserva

class LaboratorioForm(forms.ModelForm):
    class Meta:
        model = Laboratorio
        fields = "__all__"

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = "__all__"