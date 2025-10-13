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
