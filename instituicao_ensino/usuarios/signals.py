
"""
Sinais do app de usuários.
Define integrações automáticas para login, criação de usuários e envio de e-mails de boas-vindas.
"""

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
    """
    Enfileira o envio de e-mail de boas-vindas e confirmação para o novo usuário.
    Não interrompe o fluxo em caso de erro no envio.
    """
    try:
        if not usuario or not usuario.user or not usuario.email:
            return
        # Monta link de confirmação (opcional; conta já ativa para testes)
        uid = urlsafe_base64_encode(force_bytes(usuario.user.pk))
        token = default_token_generator.make_token(usuario.user)
        path = reverse('confirmar_email', kwargs={'uidb64': uid, 'token': token})
        site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
        confirm_url = f"{site_url}{path}" if site_url else path

        # Renderiza templates e enfileira o e-mail
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
        # Não interrompe criação do usuário em caso de erro no e-mail
        pass


@receiver(user_logged_in)
def link_usuario_on_login(sender, user, request, **kwargs):
    """
    Ao realizar login, associa o Django User ao Usuario correspondente (pelo nome de usuário).
    Garante o vínculo entre contas criadas via formulário ou admin e mantém a sessão compatível.
    """
    try:
        perfil = Usuario.objects.get(nome_usuario=user.username)
        if not perfil.user:
            perfil.user = user
            perfil.save()
        # garante id de sessão legado para outros fluxos
        request.session['usuario_id'] = perfil.id
    except Usuario.DoesNotExist:
        # nada a fazer
        pass


@receiver(post_save, sender=Usuario)
def audit_usuario_created(sender, instance, created, **kwargs):
    """
    Registra auditoria quando um Usuario do sistema é criado e garante Perfil e e-mail de boas-vindas.
    """
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
    """
    Registra auditoria quando um Django auth.User é criado e tenta vincular ao Usuario correspondente.
    """
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
