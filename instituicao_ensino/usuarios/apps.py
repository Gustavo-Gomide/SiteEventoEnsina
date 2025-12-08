"""
Configuração do aplicativo Django para o app de usuários.
Inclui inicialização de sinais e criação automática de superusuário admin, se necessário.
"""

from django.apps import AppConfig

class UsuariosConfig(AppConfig):
    """
    AppConfig para o app 'usuarios'.
    Define configurações padrão e executa inicializações customizadas ao iniciar o app.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "usuarios"

    def ready(self):
        """
        Executa inicializações ao carregar o app:
        - Registra os signal handlers do app.
        - Cria automaticamente um superusuário 'admin' caso não exista, exceto durante migrações, testes ou coletstatic.
        - Lida com possíveis exceções para evitar falhas na inicialização.
        """
        # Registra os signal handlers do app
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Ignora falhas ao registrar sinais para não bloquear o startup
            pass

        # Evita acessar o banco de dados durante comandos sensíveis (migrações, testes, coletstatic)
        try:
            import sys
            from django.contrib.auth import get_user_model
            from django.db import ProgrammingError, OperationalError

            # Não execute durante migrações, testes ou coletstatic
            argv = sys.argv if hasattr(sys, 'argv') else []
            if any(cmd in argv for cmd in ('migrate', 'makemigrations', 'collectstatic', 'test')):
                return

            UserModel = get_user_model()
            # Cria superusuário admin padrão se não existir
            if not UserModel.objects.filter(username='admin').exists():
                UserModel.objects.create_superuser(username='admin', email='', password='123456')
        except (ProgrammingError, OperationalError):
            # DB não está pronto; ignora criação automática
            pass
        except Exception:
            # Qualquer outra exceção não deve bloquear a inicialização
            pass
