from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Usuario
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from .utils import log_audit


@receiver(user_logged_in)
def link_usuario_on_login(sender, user, request, **kwargs):
    """When a Django User logs in, try to associate it with an existing Usuario
    that has the same username (nome_usuario). This provides a robust mapping
    for existing users created via the registration form or admin.
    """
    try:
        perfil = Usuario.objects.get(nome_usuario=user.username)
        if not perfil.user:
            perfil.user = user
            perfil.save()
        # ensure legacy session id is present for other code paths
        request.session['usuario_id'] = perfil.id
    except Usuario.DoesNotExist:
        # nothing to do
        pass


@receiver(post_save, sender=Usuario)
def audit_usuario_created(sender, instance, created, **kwargs):
    """Registra auditoria quando um Usuario do sistema é criado."""
    try:
        if created:
            # usuário lógico criado
            log_audit(usuario=instance, action='create_usuario', object_type='Usuario', object_id=instance.id, description=f'Usuario criado: {instance.nome_usuario}')
    except Exception:
        pass


@receiver(post_save, sender=User)
def audit_authuser_created(sender, instance, created, **kwargs):
    """Registra auditoria quando um Django auth.User é criado."""
    try:
        if created:
            # tenta vincular usuario profile se existir
            perfil = None
            try:
                perfil = Usuario.objects.filter(nome_usuario=instance.username).first()
            except Exception:
                perfil = None

            log_audit(django_user=instance, usuario=perfil, action='create_django_user', object_type='auth.User', object_id=instance.id, description=f'Auth User criado: {instance.username}')
    except Exception:
        pass
