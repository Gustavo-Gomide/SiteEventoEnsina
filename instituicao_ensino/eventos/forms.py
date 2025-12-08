from django import forms
from .models import Evento, TipoEvento
from django.utils import timezone

class EventoForm(forms.ModelForm):
    tipo = forms.ModelChoiceField(
        queryset=TipoEvento.objects.all(),
        empty_label="Selecione o tipo",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Evento
        fields = [
            'titulo', 'tipo', 'modalidade', 'data_inicio', 'data_fim',
            'horario', 'local', 'link', 'quantidade_participantes',
            'sem_limites', 'descricao', 'thumb', 'horas'
        ]
        widgets = {
            'data_inicio': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'horario': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),
            'quantidade_participantes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'local': forms.TextInput(attrs={'class': 'form-control'}),
            'link': forms.URLInput(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'modalidade': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'horas': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.5, 'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # força valor inicial dos campos de data/hora para compatibilidade com HTML
        # também define o mínimo permitido para datas como a data atual
        today_str = timezone.localdate().strftime('%Y-%m-%d')
        if 'min' not in self.fields['data_inicio'].widget.attrs:
            self.fields['data_inicio'].widget.attrs['min'] = today_str
        if 'min' not in self.fields['data_fim'].widget.attrs:
            self.fields['data_fim'].widget.attrs['min'] = today_str
        if self.instance and self.instance.pk:
            if self.instance.data_inicio:
                self.fields['data_inicio'].initial = self.instance.data_inicio.strftime('%Y-%m-%d')
            if self.instance.data_fim:
                self.fields['data_fim'].initial = self.instance.data_fim.strftime('%Y-%m-%d')
            if self.instance.horario:
                self.fields['horario'].initial = self.instance.horario.strftime('%H:%M')

    def clean_data_inicio(self):
        data_inicio = self.cleaned_data.get('data_inicio')
        if data_inicio and data_inicio < timezone.localdate():
            raise forms.ValidationError("A data de início não pode ser anterior à data atual.")
        return data_inicio

    def clean_data_fim(self):
        data_inicio = self.cleaned_data.get('data_inicio')
        data_fim = self.cleaned_data.get('data_fim')
        if data_fim and data_inicio and data_fim < data_inicio:
            raise forms.ValidationError("A data final não pode ser menor que a data de início.")
        return data_fim
