from django.contrib import admin
from .models import TipoEvento, Evento
from .models import InscricaoEvento


# -------------------------------
# Admin para TipoEvento
# -------------------------------
@admin.register(TipoEvento)
class TipoEventoAdmin(admin.ModelAdmin):
    # Campos exibidos na lista
	list_display = ('id', 'tipo')
    # Permite busca rápida pelo nome do tipo
	search_fields = ('tipo',)


# -------------------------------
# Admin para Evento
# -------------------------------
@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    # Campos exibidos na lista
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
    # Campos exibidos na lista
	list_display = ('evento', 'inscrito', 'data_inscricao', 'is_validated')
    # Filtros laterais na tela do admin
	list_filter = ('is_validated', 'evento')
    # Campos que podem ser buscados no admin
	search_fields = ('inscrito__nome_usuario', 'inscrito__nome')
    # Não colocamos autocomplete_fields aqui para evitar erro E040
