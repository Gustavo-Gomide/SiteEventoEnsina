from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from .models import EmailJob
from .worker import push_job
import socket


def enqueue_email(to_email: str, subject: str, *, text_body: str = None, html_body: str = None, attachments=None, when=None, send_now: bool = False):
    """Add a new email to the queue. A background worker (same process) will send it."""
    # If immediate send requested, send synchronously to avoid duplicate processing
    if send_now:
        # Ensure a valid sender to avoid SMTP rejection
        sender = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'SERVER_EMAIL', None)
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body or '',
            from_email=sender,
            to=[to_email],
        )
        if html_body:
            # Attach HTML and mark message as 'related' so CID images render
            msg.attach_alternative(html_body, 'text/html')
            try:
                msg.mixed_subtype = 'related'
            except Exception:
                pass
        for att in (attachments or []):
            try:
                path = att.get('path')
                name = att.get('name') or (path.split('/')[-1] if path else 'anexo')
                ctype = att.get('mimetype') or 'application/octet-stream'
                cid = att.get('cid')
                with open(path, 'rb') as f:
                    data = f.read()
                if cid and ctype.startswith('image/'):
                    # Attach inline image for CID references in HTML body
                    from email.mime.image import MIMEImage
                    img = MIMEImage(data, _subtype=ctype.split('/')[-1])
                    img.add_header('Content-ID', f'<{cid}>')
                    img.add_header('Content-Disposition', 'inline', filename=name)
                    msg.attach(img)
                else:
                    msg.attach(name, data, ctype)
            except Exception:
                continue
        # Send and log any failure with context
        try:
            msg.send(fail_silently=False)
        except Exception as e:
            import logging, traceback
            logger = logging.getLogger(__name__)
            logger.error("Email send failed: subject=%s to=%s error=%s\n%s", subject, to_email, e, traceback.format_exc())
            # Re-raise to surface the error to caller flows (so UI can show message)
            raise
        return None

    job = EmailJob.objects.create(
        to_email=to_email,
        subject=subject,
        text_body=text_body or '',
        html_body=html_body or '',
        attachments=attachments or [],
        scheduled_at=when or timezone.now(),
    )
    # Mark as sending and push into socket to avoid DB pollers claiming it simultaneously
    pushed = False
    try:
        # Set to 'sending' as a lock before pushing to socket; workers will process and set to 'sent'
        from django.utils import timezone as _tz
        EmailJob.objects.filter(pk=job.pk, status='pending').update(status='sending', updated_at=_tz.now())
        # Try in-process queue first
        if push_job(job.id):
            pushed = True
        else:
            # Try TCP socket push fallback
            try:
                host = '127.0.0.1'
                port = int(getattr(settings, 'EMAIL_QUEUE_PORT', 9099))
                with socket.create_connection((host, port), timeout=1.0) as s:
                    s.sendall(f"{job.id}\n".encode('utf-8'))
                    pushed = True
            except Exception:
                pushed = False
    except Exception:
        pushed = False
    # If we failed to push to socket, revert status back to pending so poller/worker can claim it later
    if not pushed:
        from django.utils import timezone as _tz
        EmailJob.objects.filter(pk=job.pk, status='sending').update(status='pending', updated_at=_tz.now())
    return job


def queue_welcome_confirmation_email(user, usuario, *, send_now: bool = False):
    """Queue welcome email with confirmation link for a Django `User` and its `Usuario` profile."""
    if not user or not getattr(usuario, 'email', None):
        return None

    # Build confirmation link
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    from django.contrib.auth.tokens import default_token_generator

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    path = reverse('confirmar_email', kwargs={'uidb64': uid, 'token': token})

    site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
    confirm_url = f"{site_url}{path}" if site_url else path

    ctx = {
        'usuario': usuario,
        'user': user,
        'confirm_url': confirm_url,
        'site_url': site_url,
        'static_url': getattr(settings, 'STATIC_URL', '/static/'),
        'system_name': 'EventoEnsina',
    }

    subject = f"Bem-vindo ao EventoEnsina, {usuario.nome.split(' ')[0]}! Confirme seu cadastro"
    text = render_to_string('emails/welcome_confirmation.txt', ctx)
    html = render_to_string('emails/welcome_confirmation.html', ctx)
    attachments = []
    try:
        favicon_path = settings.BASE_DIR / 'instituicao_ensino' / 'static' / 'favicon.png'
        attachments.append({'path': str(favicon_path), 'name': 'favicon.png', 'mimetype': 'image/png', 'cid': 'sg-logo'})
    except Exception:
        pass
    return enqueue_email(usuario.email, subject, text_body=text, html_body=html, attachments=attachments, send_now=True)


def queue_certificate_ready_email(usuario, cert, evento=None, *, send_now: bool = False):
    """Queue certificate ready email with link and optional attachment."""
    if not getattr(usuario, 'email', None):
        return None

    site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
    # Button should always lead to the user's public certificates page
    try:
        path = reverse('perfil_certificados', kwargs={'nome_usuario': usuario.nome_usuario})
        cert_url = f"{site_url}{path}" if site_url else path
    except Exception:
        cert_url = None

    # Prefer hosted HTTPS logo URL; fall back to SITE_URL + static path
    logo_url = None
    try:
        logo_url = getattr(settings, 'EMAIL_LOGO_URL', None)
        if not logo_url:
            static_path = '/static/images/email_logo.png'
            logo_url = f"{site_url}{static_path}" if site_url else static_path
    except Exception:
        logo_url = None

    ctx = {
        'usuario': usuario,
        'cert': cert,
        'evento': evento,
        'cert_url': cert_url,
        'site_url': site_url,
        'system_name': 'EventoEnsina',
        'logo_url': logo_url,
    }
    subject = f"Seu certificado está disponível{f' - {evento.titulo}' if evento else ''}"
    text = render_to_string('emails/certificate_ready.txt', ctx)
    html = render_to_string('emails/certificate_ready.html', ctx)

    attachments = []
    # Inline favicon/logo as CID for email template
    # No need to attach logo when using base64 data URI
    # Attach PDF if available
    try:
        if getattr(cert, 'pdf', None) and getattr(cert.pdf, 'path', None):
            attachments.append({'path': cert.pdf.path, 'name': getattr(cert.pdf, 'name', 'certificado.pdf').split('/')[-1], 'mimetype': 'application/pdf'})
    except Exception:
        pass

    return enqueue_email(usuario.email, subject, text_body=text, html_body=html, attachments=attachments, send_now=True)


def queue_password_recovery_email(user, usuario=None, *, login_url: str = None, send_now: bool = False):
    """Send password recovery email with a direct login link to profile.

    Uses a one-time token to authenticate, then the user can change the password.
    """
    to_email = None
    if usuario and getattr(usuario, 'email', None):
        to_email = usuario.email
    elif getattr(user, 'email', None):
        to_email = user.email
    if not to_email or not login_url:
        return None

    site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
    # Compute a friendly first name for greeting
    def _first_name():
        try:
            if getattr(user, 'first_name', None):
                return user.first_name
            if usuario and getattr(usuario, 'nome', None):
                return (usuario.nome or '').split(' ')[0]
        except Exception:
            pass
        return getattr(user, 'username', '')

    ctx = {
        'usuario': usuario,
        'user': user,
        'first_name': _first_name(),
        'login_url': login_url,
        'site_url': site_url,
        'system_name': 'EventoEnsina',
    }
    subject = 'Recuperação de acesso — EventoEnsina'
    text = render_to_string('emails/recuperar_senha.txt', ctx)
    html = render_to_string('emails/recuperar_senha.html', ctx)
    attachments = []
    try:
        favicon_path = settings.BASE_DIR / 'instituicao_ensino' / 'static' / 'favicon.png'
        attachments.append({'path': str(favicon_path), 'name': 'favicon.png', 'mimetype': 'image/png', 'cid': 'sg-logo'})
    except Exception:
        pass
    return enqueue_email(to_email, subject, text_body=text, html_body=html, attachments=attachments, send_now=True)
