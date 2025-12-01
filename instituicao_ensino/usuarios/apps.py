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
        # Garante que exista um usuário Django chamado 'admin' com a senha '123456'.
        # Envolvemos em try/except para evitar problemas durante migrações ou quando o DB
        # ainda não estiver pronto (testes e comandos manage.py podem rodar antes).
        try:
            from django.contrib.auth.models import User
            from django.db import ProgrammingError, OperationalError

            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser(username='admin', email='', password='123456')
        except (ProgrammingError, OperationalError):
            # DB não está pronto; ignora criação automática
            pass
        except Exception:
            # Qualquer outra exceção não deve bloquear a inicialização
            pass
