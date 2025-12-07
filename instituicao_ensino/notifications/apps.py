from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        # Import signals if we add any later
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
        # Start background email worker (runs inside runserver process)
        # Start background worker only in the main runserver process (avoid double start on autoreload)
        try:
            import os
            run_main = os.environ.get('RUN_MAIN')
            if run_main == 'true' or run_main is None:
                from .worker import start_background_worker
                start_background_worker(interval_seconds=5)
        except Exception:
            # Don't break app initialization if worker fails
            pass
