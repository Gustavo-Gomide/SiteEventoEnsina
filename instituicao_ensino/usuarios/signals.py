from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Usuario
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from .utils import log_audit
from .models import Perfil
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.conf import settings

def _queue_welcome_email(usuario: Usuario):
    try:
        if not usuario or not usuario.user or not usuario.email:
            return
        # Build confirmation link (opcional; conta já ativa para testes)
        uid = urlsafe_base64_encode(force_bytes(usuario.user.pk))
        token = default_token_generator.make_token(usuario.user)
        path = reverse('confirmar_email', kwargs={'uidb64': uid, 'token': token})
        site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
        confirm_url = f"{site_url}{path}" if site_url else path

        # Render templates and enqueue email
        from notifications.services import enqueue_email
        from django.template.loader import render_to_string
        ctx = {
            'usuario': usuario,
            'user': usuario.user,
            'confirm_url': confirm_url,
            'site_url': site_url,
            'static_url': getattr(settings, 'STATIC_URL', '/static/'),
            'system_name': 'SGEA',
        }
        subject = f"Bem-vindo ao SGEA, {usuario.nome.split(' ')[0]}! Confirme seu cadastro"
        text = render_to_string('emails/welcome_confirmation.txt', ctx)
        html = render_to_string('emails/welcome_confirmation.html', ctx)
        enqueue_email(usuario.email, subject, text_body=text, html_body=html)
    except Exception:
        # Do not break user creation on email errors
        pass


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
            # Garante Perfil associado
            try:
                Perfil.objects.get_or_create(usuario=instance)
            except Exception:
                pass
            _queue_welcome_email(instance)
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
