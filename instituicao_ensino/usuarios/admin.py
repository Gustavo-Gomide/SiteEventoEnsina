
"""
Configuração do Django Admin para os modelos de usuários, instituições e logs de auditoria.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import TipoUsuario, Instituicao, Usuario, Perfil

# Registro básico dos modelos principais de usuários e instituições
admin.site.register(TipoUsuario)
admin.site.register(Instituicao)
admin.site.register(Usuario)
admin.site.register(Perfil)

from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
	"""
	Configuração da interface de administração para o modelo AuditLog.
	Permite visualizar, filtrar e buscar logs de auditoria do sistema.
	"""
	list_display = ('timestamp', 'usuario', 'django_user', 'action', 'object_type', 'object_id')
	list_filter = ('action', 'object_type', 'timestamp')
	search_fields = ('description', 'object_id')
	readonly_fields = ('timestamp',)
	date_hierarchy = 'timestamp'