from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Usuario


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
