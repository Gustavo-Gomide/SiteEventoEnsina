
"""
Configurações de administração do Django para os modelos de eventos.

Este módulo define as classes de administração para os modelos TipoEvento, Evento e InscricaoEvento,
permitindo customização das telas de administração, filtros, buscas e exibição de campos.
"""

from django.contrib import admin
from .models import TipoEvento, Evento
from .models import InscricaoEvento



# -------------------------------
# Admin para TipoEvento
# -------------------------------
@admin.register(TipoEvento)
class TipoEventoAdmin(admin.ModelAdmin):
    """
    Configuração da interface de administração para o modelo TipoEvento.

    - list_display: exibe os campos 'id' e 'tipo' na listagem.
    - search_fields: permite busca pelo campo 'tipo'.
    """
    # Campos exibidos na lista de tipos de evento
    list_display = ('id', 'tipo')
    # Permite busca rápida pelo nome do tipo
    search_fields = ('tipo',)



# -------------------------------
# Admin para Evento
# -------------------------------
@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    """
    Configuração da interface de administração para o modelo Evento.

    - list_display: exibe campos principais do evento na listagem.
    - list_filter: permite filtrar eventos por modalidade e tipo.
    - search_fields: permite busca por título e organizador.
    """
    # Campos exibidos na lista de eventos
    list_display = ('titulo', 'tipo', 'modalidade', 'data_inicio', 'data_fim', 'organizador', 'thumb')
    # Filtros laterais na tela do admin
    list_filter = ('modalidade', 'tipo')
    # Barra de pesquisa
    search_fields = ('titulo', 'organizador')



# -------------------------------
# Admin para InscricaoEvento
# -------------------------------
@admin.register(InscricaoEvento)
class InscricaoEventoAdmin(admin.ModelAdmin):
    """
    Configuração da interface de administração para o modelo InscricaoEvento.

    - list_display: exibe informações da inscrição, usuário e status de validação.
    - list_filter: permite filtrar inscrições por status de validação e evento.
    - search_fields: permite busca por nome de usuário e nome do inscrito.
    """
    # Campos exibidos na lista de inscrições
    list_display = ('evento', 'inscrito', 'data_inscricao', 'is_validated')
    # Filtros laterais na tela do admin
    list_filter = ('is_validated', 'evento')
    # Campos que podem ser buscados no admin
    search_fields = ('inscrito__nome_usuario', 'inscrito__nome')
    # Não colocamos autocomplete_fields aqui para evitar erro E040
