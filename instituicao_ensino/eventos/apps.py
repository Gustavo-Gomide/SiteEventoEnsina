"""
Configuração da aplicação Django 'eventos'.

Define a classe de configuração da app, incluindo o campo padrão de ID e o nome da aplicação.
O método ready() é utilizado para registrar sinais customizados ao iniciar a aplicação.
"""

from django.apps import AppConfig

# -------------------------------
# Configuração da aplicação "eventos"
# -------------------------------
class EventoConfig(AppConfig):
    """
    Classe de configuração da aplicação 'eventos'.

    - default_auto_field: Define o tipo de campo padrão para IDs dos modelos (BigAutoField).
    - name: Nome interno da aplicação para uso no Django.
    - ready(): Executa código de inicialização, como o registro de sinais.
    """
    # Campo padrão de ID para modelos criados nesta app
    # BigAutoField cria automaticamente um campo inteiro grande (64-bit) para a primary key
    default_auto_field = "django.db.models.BigAutoField"
    
    # Nome da aplicação, usado internamente pelo Django e para referências no settings.INSTALLED_APPS
    name = "eventos"

    def ready(self):
        """
        Executa rotinas de inicialização da app, como o registro de sinais customizados.
        """
        # Registra sinais definidos no módulo signals.py
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
