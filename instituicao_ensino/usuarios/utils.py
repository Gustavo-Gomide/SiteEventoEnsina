"""
Utility helpers for user media and certificate rendering.

Provides:
- create_user_dirs(usuario): ensure per-user directories exist under
    MEDIA_ROOT so that file uploads and generated certificates have a stable
    place to be stored.
- render_and_save_html_certificate(cert_obj, evento, aluno): when binary
    generation libraries are missing (Pillow/reportlab/qrcode) we still want
    to present a certificate via the web. This helper renders the certificate
    template to HTML and saves it as the `arquivo` on the Certificado model.
"""

from django.template.loader import render_to_string
from django.core.files.base import ContentFile
import os
from django.conf import settings
import logging


def create_user_dirs(usuario):
    """Ensure base directories for a Usuario exist under MEDIA_ROOT.

    Creates: media/<base_dir>/foto_perfil and media/<base_dir>/certificados
    """
    logger = logging.getLogger(__name__)
    try:
        # ensure MEDIA_ROOT exists and is writable
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if not media_root:
            logger.error('MEDIA_ROOT not configured in settings')
            return False
        # prefer the stored base_dir so paths stay stable
        base = getattr(usuario, 'base_dir', None)
        if not base:
            nome_clean = str(usuario.nome_usuario).replace(' ', '_')
            instituicao = usuario.instituicao.nome if usuario.instituicao else 'sem_instituicao'
            instituicao_clean = str(instituicao).replace(' ', '_')
            base = f'usuarios/{nome_clean}_{instituicao_clean}'
            # persist base_dir so future saves use the stable path
            try:
                usuario.base_dir = base
                usuario.save()
            except Exception:
                # don't fail creation if saving base_dir is not possible
                logger.debug('Não foi possível persistir base_dir para usuario %s', getattr(usuario, 'id', None))
        foto_dir = os.path.join(media_root, base, 'foto_perfil')
        cert_dir = os.path.join(media_root, base, 'certificados')
        os.makedirs(foto_dir, exist_ok=True)
        os.makedirs(cert_dir, exist_ok=True)
        return True
    except Exception as e:
        logger.exception(f'Erro criando diretorios de usuario {getattr(usuario, "id", None)}: {e}')
        return False
    
from PIL import Image
import os
from django.conf import settings

def resize_image(path, max_size=(400, 400), quality=70):
    if not os.path.exists(path):
        return
    with Image.open(path) as img:
        # Pillow 10+ usa Resampling.LANCZOS no lugar de ANTIALIAS
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        img.save(path, quality=quality)


def log_audit(request=None, usuario=None, django_user=None, action=None, object_type=None, object_id=None, description=None, extra=None):
    """Cria um registro em AuditLog de forma segura (import tardio para evitar ciclos).

    Parâmetros:
    - request: objeto HttpRequest opcional (usado para extrair IP)
    - usuario: instância de usuarios.Usuario quando aplicável
    - django_user: instância de auth.User quando aplicável
    - action: string curta representando a ação
    - object_type/object_id: tipo e id do objeto afetado
    - description: texto adicional
    - extra: dicionário JSON-serializável com dados extras
    """
    if not action:
        return None

    try:
        # import tardio para evitar ciclos de import
        from .models import AuditLog
        ip = None
        if request is not None:
            xff = request.META.get('HTTP_X_FORWARDED_FOR')
            if xff:
                ip = xff.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')

        # cria o registro
        AuditLog.objects.create(
            usuario=usuario,
            django_user=django_user,
            action=str(action),
            object_type=object_type,
            object_id=str(object_id) if object_id is not None else None,
            description=description,
            ip_address=ip,
            extra=extra
        )
    except Exception:
        # não propagar erros de auditoria para a aplicação
        logging.getLogger(__name__).exception('Falha ao gravar AuditLog')
    return None
