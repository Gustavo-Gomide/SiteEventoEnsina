from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "usuarios"

    def ready(self):
        # register signal handlers
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
        # Evita acessar DB durante inicialização/migração; usa get_user_model após registro.
        try:
            import sys
            from django.contrib.auth import get_user_model
            from django.db import ProgrammingError, OperationalError

            # Não execute durante migrações, testes ou coletstatic
            argv = sys.argv if hasattr(sys, 'argv') else []
            if any(cmd in argv for cmd in ('migrate', 'makemigrations', 'collectstatic', 'test')):
                return

            UserModel = get_user_model()
            if not UserModel.objects.filter(username='admin').exists():
                UserModel.objects.create_superuser(username='admin', email='', password='123456')
        except (ProgrammingError, OperationalError):
            # DB não está pronto; ignora criação automática
            pass
        except Exception:
            # Qualquer outra exceção não deve bloquear a inicialização
            pass
