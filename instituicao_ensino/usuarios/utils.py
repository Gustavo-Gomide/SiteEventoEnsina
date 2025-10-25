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
