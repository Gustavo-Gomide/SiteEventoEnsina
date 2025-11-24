from django.apps import AppConfig

# -------------------------------
# Configuração da aplicação "eventos"
# -------------------------------
class EventoConfig(AppConfig):
    # Campo padrão de ID para modelos criados nesta app
    # BigAutoField cria automaticamente um campo inteiro grande (64-bit) para a primary key
    default_auto_field = "django.db.models.BigAutoField"
    
    # Nome da aplicação, usado internamente pelo Django e para referências no settings.INSTALLED_APPS
    name = "eventos"

    def ready(self):
        # register signals
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
