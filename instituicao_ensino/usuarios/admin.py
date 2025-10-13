from django.contrib import admin
from .models import TipoUsuario, Instituicao, Usuario, Perfil, DDD

# Register your models here.

admin.site.register(TipoUsuario)
admin.site.register(Instituicao)
admin.site.register(Usuario)
admin.site.register(Perfil)
admin.site.register(DDD)