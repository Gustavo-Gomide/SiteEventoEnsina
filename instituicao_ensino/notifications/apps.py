
"""
Configuração da aplicação Django 'notifications'.

Inclui inicialização de sinais e worker de envio de emails em background.
"""

from django.apps import AppConfig

class NotificationsConfig(AppConfig):
    """
    Classe de configuração da app 'notifications'.
    - Inicializa sinais (caso existam).
    - Inicia o worker de envio de emails em background ao iniciar o servidor.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        """
        Executa rotinas de inicialização da app:
        - Importa sinais (se existirem).
        - Inicia o worker de emails em background apenas no processo principal do runserver.
        """
        # Importa sinais se existirem
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
        # Inicia o worker de email em background (apenas no processo principal)
        try:
            import os
            run_main = os.environ.get('RUN_MAIN')
            if run_main == 'true' or run_main is None:
                from .worker import start_background_worker
                start_background_worker(interval_seconds=5)
        except Exception:
            # Não interrompe a inicialização da app se o worker falhar
            pass
