
"""
Formulários para manipulação de eventos na aplicação.

Define o formulário principal para criação e edição de eventos, incluindo validações customizadas e widgets personalizados.
"""

from django import forms
from .models import Evento, TipoEvento
from django.utils import timezone


class EventoForm(forms.ModelForm):
    """
    Formulário para criação e edição de eventos.

    Inclui validações customizadas para datas e widgets personalizados para melhor experiência do usuário.
    """
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
        """
        Inicializa o formulário, ajustando valores iniciais e restrições dos campos de data/hora.
        Define o valor mínimo das datas como a data atual e preenche valores iniciais ao editar.
        """
        super().__init__(*args, **kwargs)
        # Força valor inicial dos campos de data/hora para compatibilidade com HTML
        # Também define o mínimo permitido para datas como a data atual
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
        """
        Valida se a data de início não é anterior à data atual.
        """
        data_inicio = self.cleaned_data.get('data_inicio')
        if data_inicio and data_inicio < timezone.localdate():
            raise forms.ValidationError("A data de início não pode ser anterior à data atual.")
        return data_inicio

    def clean_data_fim(self):
        """
        Valida se a data final não é menor que a data de início.
        """
        data_inicio = self.cleaned_data.get('data_inicio')
        data_fim = self.cleaned_data.get('data_fim')
        if data_fim and data_inicio and data_fim < data_inicio:
            raise forms.ValidationError("A data final não pode ser menor que a data de início.")
        return data_fim
