from django import forms
from .models import Disponibilidade, Laboratorio

class DisponibilidadeForm(forms.ModelForm):
    class Meta:
        model = Disponibilidade
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        if self.instance.data:
            self.initial['data'] = self.instance.data.strftime('%Y-%m-%d')

        if self.instance.horario_inicio:
            self.initial['horario_inicio'] = self.instance.horario_inicio.strftime('%H:%M')

        if self.instance.horario_fim:
            self.initial['horario_fim'] = self.instance.horario_fim.strftime('%H:%M')

        self.fields['data'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['horario_inicio'].widget = forms.TimeInput(attrs={'type': 'time'})
        self.fields['horario_fim'].widget = forms.TimeInput(attrs={'type': 'time'})

class LaboratorioForm(forms.ModelForm):
    class Meta:
        model = Laboratorio
        fields = "__all__"