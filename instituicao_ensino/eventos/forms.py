from django import forms
from .models import Evento, TipoEvento

# -------------------------------
# Formulário para criação/edição de eventos
# -------------------------------
class EventoForm(forms.ModelForm):
    # Campo 'tipo' personalizado:
    # - queryset define os registros disponíveis (todos os Tipos de Evento)
    # - empty_label define o texto exibido quando nenhum tipo está selecionado
    # - widget aplica a classe CSS Bootstrap 'form-select'
    tipo = forms.ModelChoiceField(
        queryset=TipoEvento.objects.all(),
        empty_label="Selecione o tipo",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        # Modelo que este formulário manipula
        model = Evento
        # Campos que aparecerão no formulário
        fields = [
            'titulo', 'tipo', 'modalidade', 'data_inicio', 'data_fim',
            'horario', 'local', 'link', 'quantidade_participantes',
            'sem_limites', 'descricao', 'thumb', 'horas'
        ]
        # Widgets definem como os campos aparecerão no HTML
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'horario': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'quantidade_participantes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'local': forms.TextInput(attrs={'class': 'form-control'}),
            'link': forms.URLInput(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'modalidade': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'horas': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.5, 'min': 0}),
        }

    # -------------------------------
    # Validação personalizada do formulário
    # -------------------------------
    def clean_data_fim(self):
        """
        Garante que a data final não seja menor que a data de início.
        - cleaned_data contém os dados já validados pelo formulário.
        - Se houver erro, é lançada uma ValidationError que será exibida no formulário.
        """
        data_inicio = self.cleaned_data.get('data_inicio')
        data_fim = self.cleaned_data.get('data_fim')

        if data_fim and data_inicio and data_fim < data_inicio:
            raise forms.ValidationError("A data final não pode ser menor que a data de início.")

        # Retorna o valor limpo da data_fim
        return data_fim
