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


# def render_and_save_html_certificate(cert_obj, evento, aluno):
#     """Renderiza o template de certificado para HTML e salva em cert_obj.arquivo."""
#     try:
#         # assemble context expected by certificado_base.html
#         instituicao_nome = getattr(settings, 'INSTITUICAO_NOME', 'Instituição')
#         logo_url = getattr(settings, 'INSTITUTION_LOGO_URL', settings.STATIC_URL + 'images/default_profile.png')

#         # build public url if public_id present
#         site = getattr(settings, 'SITE_URL', '').rstrip('/')
#         if getattr(cert_obj, 'public_id', None):
#             if site:
#                 qr_url = f"{site}/usuarios/certificado/{cert_obj.public_id}/"
#             else:
#                 qr_url = f"/usuarios/certificado/{cert_obj.public_id}/"
#         else:
#             qr_url = ''

#         context = {
#             'evento': evento,
#             'usuario': aluno,
#             'certificado': cert_obj,
#             'nome_participante': aluno.nome,
#             'nome_evento': evento.titulo if evento else '',
#             'data_inicio': evento.data_inicio.strftime('%d/%m/%Y') if getattr(evento, 'data_inicio', None) else '',
#             'data_fim': evento.data_fim.strftime('%d/%m/%Y') if getattr(evento, 'data_fim', None) else '',
#             'horas': getattr(cert_obj, 'horas', None),
#             'qr_url': qr_url,
#             'instituicao_nome': instituicao_nome,
#             'logo_url': logo_url,
#         }
#         html = render_to_string('certificado_base.html', context)
#         filename = f'certificado_{evento.id}_{aluno.id}.html'

#         # Ensure directories exist and cert has stable base_dir
#         try:
#             create_user_dirs(aluno)
#         except Exception:
#             pass

#         # mark upload field so user_directory_path stores under certificados/
#         try:
#             setattr(cert_obj, '_upload_field', 'certificados')
#         except Exception:
#             pass

#         # ensure cert instance is saved before attaching files so upload_to has base
#         try:
#             cert_obj.save()
#         except Exception:
#             pass

#         # attach HTML fallback
#         cert_obj.arquivo.save(filename, ContentFile(html.encode('utf-8')), save=True)

#         # ensure public_id exists for validation URLs/QRs
#         try:
#             if not cert_obj.public_id:
#                 import uuid
#                 cert_obj.public_id = str(uuid.uuid4())
#                 cert_obj.save()
#         except Exception:
#             pass

#         return True
#     except Exception:
#         return False
