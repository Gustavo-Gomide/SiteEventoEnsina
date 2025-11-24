from django.contrib import admin
from .models import TipoUsuario, Instituicao, Usuario, Perfil, DDD

# Register your models here.

admin.site.register(TipoUsuario)
admin.site.register(Instituicao)
admin.site.register(Usuario)
admin.site.register(Perfil)
admin.site.register(DDD)

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
	list_display = ('timestamp', 'usuario', 'django_user', 'action', 'object_type', 'object_id')
	list_filter = ('action', 'object_type', 'timestamp')
	search_fields = ('description', 'object_id')
	readonly_fields = ('timestamp',)
	date_hierarchy = 'timestamp'