from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Evento, InscricaoEvento
from usuarios.utils import log_audit


@receiver(post_save, sender=Evento)
def audit_evento_saved(sender, instance, created, **kwargs):
    try:
        action = 'create_event' if created else 'update_event'
        usuario = getattr(instance, 'criador', None)
        log_audit(usuario=usuario, action=action, object_type='Evento', object_id=instance.id, description=f'Evento {action}: {instance.titulo}')
    except Exception:
        pass


@receiver(post_delete, sender=Evento)
def audit_evento_deleted(sender, instance, **kwargs):
    try:
        usuario = getattr(instance, 'criador', None)
        log_audit(usuario=usuario, action='delete_event', object_type='Evento', object_id=getattr(instance, 'id', None), description=f'Evento excluído: {instance.titulo}')
    except Exception:
        pass


@receiver(post_save, sender=InscricaoEvento)
def audit_inscricao_saved(sender, instance, created, **kwargs):
    try:
        usuario = getattr(instance, 'inscrito', None)
        action = 'create_inscription' if created else 'update_inscription'
        log_audit(usuario=usuario, action=action, object_type='InscricaoEvento', object_id=instance.id, description=f'Inscrição {action} em evento {getattr(instance.evento, "titulo", "?")}')
    except Exception:
        pass


@receiver(post_delete, sender=InscricaoEvento)
def audit_inscricao_deleted(sender, instance, **kwargs):
    try:
        usuario = getattr(instance, 'inscrito', None)
        log_audit(usuario=usuario, action='delete_inscription', object_type='InscricaoEvento', object_id=getattr(instance, 'id', None), description=f'Inscrição excluída de evento {getattr(instance.evento, "titulo", "?")}')
    except Exception:
        pass
