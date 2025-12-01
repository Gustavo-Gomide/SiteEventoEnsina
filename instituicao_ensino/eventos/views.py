"""
Event views: criação, gerenciamento, galeria e fluxos de certificados.

Responsabilidades principais:
- Permitir que organizadores criem e gerenciem eventos (`criar_evento`,
  `meus_eventos`, `gerenciar_evento`).
- Gerar certificados web-only, com fallback para HTML se bibliotecas faltarem.
- Fornecer galeria de fotos em MEDIA_ROOT/galeria/<gallery_slug>/.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json
from django.conf import settings
import os
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging
from eventos.models import Evento
from django.utils.text import slugify
from usuarios.models import Usuario
from .models import Evento, InscricaoEvento
from .forms import EventoForm
from usuarios.views import get_current_usuario
from instituicao_ensino.views import nav_items
from django.http import FileResponse
from usuarios.utils import log_audit

# -------------------------------------------------------------------
# Função utilitária: verifica se o usuário é dono ou staff
# -------------------------------------------------------------------
def _is_event_owner(request, usuario_obj, ev):
    """
    Retorna True se o usuário for o criador (organizador) do evento,
    ou se for staff. Professores que não criaram o evento não têm acesso.
    """
    try:
        # Organizador/dono do evento
        if ev.criador and usuario_obj and ev.criador.id == usuario_obj.id:
            return True

        # Staff sempre tem acesso
        if request.user.is_authenticated and getattr(request.user, 'is_staff', False):
            return True

        # Professor que não é criador: não tem acesso
        if usuario_obj and getattr(usuario_obj.tipo, 'tipo', '').lower() == 'professor':
            return False

        return False
    except Exception:
        return False
    

# -------------------------------------------------------------------
# Criar novo evento
# -------------------------------------------------------------------
@login_required
def criar_evento(request):
    usuario = get_current_usuario(request)
    if not usuario or usuario.tipo.tipo not in ['Professor', 'Funcionario', 'Organizador']:
        messages.error(request, 'Acesso negado: é necessário estar logado como criador de eventos.')
        return redirect('login')

    if request.method == "POST":
        form = EventoForm(request.POST, request.FILES)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.criador = usuario
            evento.organizador = getattr(usuario, 'nome_usuario', getattr(usuario, 'nome', ''))

            if getattr(evento, 'sem_limites', False):
                evento.quantidade_participantes = None

            # Gera slug único para a pasta do evento
            data_str = evento.data_inicio.strftime('%Y_%m_%d') if evento.data_inicio else 'sem_data'
            nome_slug = slugify(evento.titulo)
            evento_folder = f"{data_str}_{nome_slug}"

            # Atualiza gallery_slug e cria pastas
            evento.gallery_slug = evento_folder
            galeria_path = os.path.join(settings.MEDIA_ROOT, 'eventos', evento_folder, 'galeria')
            os.makedirs(galeria_path, exist_ok=True)

            # Cria pasta do evento para thumb
            thumb_path = os.path.join(settings.MEDIA_ROOT, 'eventos', evento_folder)
            os.makedirs(thumb_path, exist_ok=True)

            evento.save()
            # Auditoria: criação de evento
            try:
                log_audit(request=request, usuario=usuario, action='create_event', object_type='Evento', object_id=evento.id, description=f'Evento criado: {evento.titulo}')
            except Exception:
                pass
            messages.success(request, "Evento criado com sucesso!")
            return redirect('lista_eventos')
    else:
        form = EventoForm()

    return render(request, 'eventos/criar_evento.html', {
        'form': form,
        'nav_items': nav_items,
        'usuario': usuario
    })


# -------------------------------------------------------------------
# Lista de eventos para inscrição - OTIMIZADA COM PAGINAÇÃO
# -------------------------------------------------------------------
def lista_eventos(request):
    usuario = get_current_usuario(request)
    
    # 1. BUSCA TODOS OS EVENTOS (passados, presentes e futuros)
    todos_eventos = Evento.objects.all().order_by('finalizado', 'data_inicio')

    # 2. PAGINAÇÃO - 10 eventos por página
    paginator = Paginator(todos_eventos, 10)
    page = request.GET.get('page', 1)
    
    try:
        eventos = paginator.page(page)
    except PageNotAnInteger:
        eventos = paginator.page(1)
    except EmptyPage:
        eventos = paginator.page(paginator.num_pages)

    # 3. Lista de inscrições do usuário
    usuario_inscricoes = []
    if usuario:
        usuario_inscricoes = list(InscricaoEvento.objects.filter(inscrito=usuario)
                                    .values_list('evento_id', flat=True))

    # 4. Prepara dados do calendário APENAS DOS EVENTOS DA PÁGINA ATUAL
    eventos_calendario = []
    for evento in todos_eventos:  # Agora só itera sobre eventos da página atual
        # Verifica disponibilidade
        inscritos = evento.inscricaoevento_set.count()
        disponivel = (evento.sem_limites or (
            evento.quantidade_participantes and 
            evento.quantidade_participantes > inscritos
        )) and evento.finalizado == False
        inscrito = usuario and evento.id in usuario_inscricoes
        
        # Prepara horário formatado
        horario_formatado = evento.horario.strftime('%H:%M') if evento.horario else ""
        
        evento_data = {
            'id': evento.id,
            'titulo': evento.titulo[:20],
            'data_inicio': evento.data_inicio.strftime('%Y-%m-%d'),
            'data_fim': evento.data_fim.strftime('%Y-%m-%d') if evento.data_fim else None,
            'disponivel': disponivel,
            'inscrito': inscrito,
            'horario': horario_formatado,
            'local': evento.local or 'Online',
            'criador_id': evento.criador.id if evento.criador else None,
        }
        eventos_calendario.append(evento_data)

    # 5. ENVIA PARA O TEMPLATE
    return render(request, 'eventos/inscrever_evento.html', {
        'eventos': eventos,                 # Para os CARDS (já paginado)
        'usuario': usuario,
        'usuario_inscricoes': usuario_inscricoes,
        'eventos_calendario': eventos_calendario, # Para o CALENDÁRIO
        'eventos_calendario_json': json.dumps(eventos_calendario, ensure_ascii=False),
    })

# -------------------------------------------------------------------
# Meus eventos (organizador ou participante)
# -------------------------------------------------------------------
@login_required
def meus_eventos(request):
    usuario = get_current_usuario(request)  # pega usuário completo

    if not usuario:
        messages.error(request, "Usuário não encontrado.")
        return redirect('main')

    is_organizador = usuario.tipo.tipo in ['Professor', 'Organizador', 'Funcionario'] if usuario.tipo else False

    eventos = []
    inscricoes = []
    evento_selecionado = None
    form = None
    inscritos = None
    usuario_inscrito_no_evento = None

    # Caso organizador
    if is_organizador:
        eventos = Evento.objects.filter(criador=usuario).order_by('-finalizado', '-data_inicio').reverse()
        inscricoes = usuario.inscricaoevento_set.select_related('evento').order_by('-evento__finalizado', '-evento__data_inicio')

        evento_id = request.GET.get('evento')
        if evento_id:
            try:
                evento_selecionado = Evento.objects.get(pk=int(evento_id))
                inscritos = evento_selecionado.inscricaoevento_set.select_related('inscrito', 'evento')
                usuario_inscrito_no_evento = InscricaoEvento.objects.filter(
                    evento=evento_selecionado,
                    inscrito=usuario
                ).first()

                if request.method == 'POST' and request.POST.get('edited_evento') == str(evento_selecionado.id):
                    form = EventoForm(request.POST, request.FILES, instance=evento_selecionado)
                    if form.is_valid():
                        ev = form.save(commit=False)
                        ev.criador = evento_selecionado.criador
                        ev.gallery_slug = ev.get_gallery_name()
                        ev.save()
                        try:
                            log_audit(request=request, usuario=usuario, action='update_event', object_type='Evento', object_id=ev.id, description=f'Evento atualizado: {ev.titulo}')
                        except Exception:
                            pass
                        messages.success(request, 'Evento atualizado com sucesso.')
                        return redirect(f"{reverse('meus_eventos')}?evento={ev.id}")
                else:
                    form = EventoForm(instance=evento_selecionado)  # pré-carrega dados existentes
            except Evento.DoesNotExist:
                evento_selecionado = None

        return render(request, 'eventos/meus_eventos.html', {
            'eventos': eventos,
            'usuario': usuario,
            'nav_items': nav_items,
            'is_organizador': True,
            'evento_selecionado': evento_selecionado,
            'form': form,
            'inscritos': inscritos,
            'inscricoes': inscricoes,
            'usuario_inscrito_no_evento': usuario_inscrito_no_evento
        })

    # Caso apenas participante
    inscricoes = usuario.inscricaoevento_set.select_related('evento').order_by('-data_inscricao')

    evento_id = request.GET.get('evento')
    if evento_id:
        try:
            evento_selecionado = Evento.objects.get(pk=int(evento_id))
            inscritos = evento_selecionado.inscricaoevento_set.select_related('inscrito', 'evento')
            usuario_inscrito_no_evento = inscricoes.filter(evento__id=evento_selecionado.id).first()
        except Evento.DoesNotExist:
            evento_selecionado = None

    return render(request, 'eventos/meus_eventos.html', {
        'inscricoes': inscricoes,
        'evento_selecionado': evento_selecionado,
        'inscritos': inscritos,
        'usuario': usuario,
        'nav_items': nav_items,
        'is_organizador': False,
        'usuario_inscrito_no_evento': usuario_inscrito_no_evento,
        'form': None
    })

# -------------------------------------------------------------------
# Gerenciar evento (validação de inscritos)
# -------------------------------------------------------------------
@login_required
def gerenciar_evento(request, evento_id):
    usuario = get_current_usuario(request)
    evento = get_object_or_404(Evento, pk=evento_id)

    if not _is_event_owner(request, usuario, evento):
        logging.warning(f'Permissão negada gerenciar_evento: evento={evento.id} usuario={getattr(usuario, "id", None)}')
        messages.error(request, 'Acesso negado: apenas o organizador pode gerenciar este evento.')
        return redirect('meus_eventos')

    inscritos = evento.inscricaoevento_set.select_related('inscrito')
    if request.method == 'POST':
        for inscr in inscritos:
            key = f'validate_{inscr.id}'
            try:
                old = inscr.is_validated
                inscr.is_validated = key in request.POST
                inscr.save()
                if old != inscr.is_validated:
                    log_audit(request=request, usuario=inscr.inscrito, action='update_inscription', object_type='InscricaoEvento', object_id=inscr.id, description=f'Inscrição {"validada" if inscr.is_validated else "desvalidada"} em evento {inscr.evento.id}')
            except Exception:
                # não interrompe o fluxo de atualização por falha na auditoria
                pass
        messages.success(request, 'Status das inscrições atualizado.')
        return redirect('gerenciar_evento', evento_id=evento.id)

    return render(request, 'eventos/gerenciar_evento.html', {
        'evento': evento,
        'inscritos': inscritos,
        'nav_items': nav_items,
        'usuario': usuario
    })

# -------------------------------------------------------------------
# Finalizar evento
# -------------------------------------------------------------------
@login_required
def finalizar_evento(request, evento_id):
    usuario = get_current_usuario(request)
    evento = get_object_or_404(Evento, pk=evento_id)
    if not _is_event_owner(request, usuario, evento):
        messages.error(request, 'Acesso negado: apenas o organizador pode finalizar este evento.')
        return redirect('meus_eventos')

    evento.finalizado = True
    evento.save()

    try:
        from usuarios.generator import generate_certificates_for_event
        generated = generate_certificates_for_event(evento.id)
        messages.success(request, f'Evento finalizado e certificados gerados: {generated}.')

        # Notificar participantes por email
        from django.core.mail import send_mail
        inscricoes_all = evento.inscricaoevento_set.select_related('inscrito')
        for ins in inscricoes_all:
            email = getattr(ins.inscrito, 'email', None)
            if email:
                try:
                    send_mail(
                        subject=f'Certificado disponível: {evento.titulo}',
                        message=f'Olá {ins.inscrito.nome}, seu certificado do evento "{evento.titulo}" está disponível.',
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                        recipient_list=[email],
                        fail_silently=True
                    )
                except Exception:
                    pass
        try:
            log_audit(request=request, usuario=usuario, action='generate_certificates', object_type='Evento', object_id=evento.id, description=f'Certificados gerados: {generated}')
        except Exception:
            pass
    except ImportError:
        from usuarios.models import Certificado
        from usuarios.utils import render_and_save_html_certificate, create_user_dirs
        for ins in evento.inscricaoevento_set.select_related('inscrito'):
            display_name = f"{evento.titulo} - {evento.data_inicio.strftime('%Y-%m-%d') if evento.data_inicio else ''}"
            try:
                create_user_dirs(ins.inscrito)
            except Exception:
                pass
            cert, created = Certificado.objects.get_or_create(usuario=ins.inscrito, evento=evento, nome=display_name)
            try:
                render_and_save_html_certificate(cert, evento, ins.inscrito)
            except Exception:
                pass
        logging.error(f'Erro ao gerar certificados na finalização do evento {evento.id}: bibliotecas ausentes')
        messages.error(request, 'Evento finalizado, mas falta biblioteca para geração; placeholders/HTML criados quando possível.')
        try:
            log_audit(request=request, usuario=usuario, action='generate_certificates_fallback', object_type='Evento', object_id=evento.id, description='Certificados gerados via fallback na finalização')
        except Exception:
            pass


    return redirect('gerenciar_evento', evento_id=evento.id)


# -------------------------------------------------------------------
# Pegar certificado individual
# -------------------------------------------------------------------
@login_required
def pegar_certificado(request, evento_id):
    """
    Gera ou retorna o certificado PDF/PNG de um usuário para um evento.
    Lógica:
    1. Verifica se o usuário está logado.
    2. Verifica se está inscrito no evento.
    3. Verifica se o evento foi finalizado.
    4. Verifica se inscrição foi aprovada.
    5. Se certificado existe e arquivo físico existe -> retorna.
    6. Se não existe -> gera certificado, salva, e retorna.
    """

    usuario = get_current_usuario(request)
    if not usuario:
        messages.error(request, 'Faça login para acessar certificados.')
        return redirect('login')

    evento = get_object_or_404(Evento, pk=evento_id)

    # Busca a inscrição do usuário
    inscr = InscricaoEvento.objects.filter(evento=evento, inscrito=usuario).first()
    if not inscr:
        messages.error(request, 'Você não está inscrito neste evento.')
        return redirect('meus_eventos')

    # Verifica evento finalizado
    if not evento.finalizado:
        messages.error(request, 'Evento ainda não finalizado. Certificados indisponíveis.')
        return redirect('detalhe_evento', evento_id=evento.id)

    # Verifica aprovação
    if not inscr.is_validated:
        messages.warning(request, 'Sua inscrição ainda não foi aprovada. Aguarde a liberação.')
        return redirect('detalhe_evento', evento_id=evento.id)

    # -------------------------------------------------------------------
    # Diretórios e nomes corretos
    # -------------------------------------------------------------------
    pasta_usuario = f"{usuario.nome_usuario}_{getattr(usuario, 'instituicao', 'sem_instituicao')}"
    cert_dir = os.path.join(settings.MEDIA_ROOT, 'usuarios', pasta_usuario, 'certificados')
    os.makedirs(cert_dir, exist_ok=True)

    nome_base = f"{slugify(evento.titulo)}_{evento.data_fim.strftime('%Y_%m_%d') if evento.data_fim else 'sem_data'}"
    pdf_path = os.path.join(cert_dir, f"{nome_base}.pdf")
    png_path = os.path.join(cert_dir, f"{nome_base}.png")

    # -------------------------------------------------------------------
    # Certificado existente no DB
    # -------------------------------------------------------------------
    from usuarios.models import Certificado
    cert = Certificado.objects.filter(usuario=usuario, evento=evento).first()

    # Se arquivo já existe no disco, abre direto
    if cert and cert.pdf and os.path.exists(cert.pdf.path):
        try:
            log_audit(request=request, usuario=usuario, action='download_certificate', object_type='Certificado', object_id=cert.id, description=f'Certificado baixado (existente) para evento {evento.id}')
        except Exception:
            pass
        return FileResponse(open(cert.pdf.path, 'rb'), content_type='application/pdf')

    # -------------------------------------------------------------------
    # Gerar certificado se não existir
    # -------------------------------------------------------------------
    try:
        from usuarios.generator import generate_certificates_for_event
        generate_certificates_for_event(evento.id)
        cert = Certificado.objects.filter(usuario=usuario, evento=evento).first()
        if cert and cert.pdf and os.path.exists(cert.pdf.path):
            try:
                log_audit(request=request, usuario=usuario, action='generate_certificate', object_type='Certificado', object_id=cert.id, description=f'Certificado gerado via generator para evento {evento.id}')
            except Exception:
                pass
            return FileResponse(open(cert.pdf.path, 'rb'), content_type='application/pdf')

    except Exception:
        # fallback HTML se generator profissional não estiver disponível
        from usuarios.utils import render_and_save_html_certificate, create_user_dirs
        create_user_dirs(usuario)

        cert, created = Certificado.objects.get_or_create(
            usuario=usuario,
            evento=evento,
            defaults={
                'nome': f"{evento.titulo} - {evento.data_fim.strftime('%Y-%m-%d') if evento.data_fim else ''}"
            }
        )
        render_and_save_html_certificate(cert, evento, usuario)

        # Atualiza pdf/relpath
        if os.path.exists(pdf_path):
            cert.pdf.name = os.path.relpath(pdf_path, settings.MEDIA_ROOT)
            cert.save(update_fields=['pdf'])
            try:
                log_audit(request=request, usuario=usuario, action='generate_certificate', object_type='Certificado', object_id=cert.id, description=f'Certificado gerado por fallback para evento {evento.id}')
            except Exception:
                pass
            return FileResponse(open(pdf_path, 'rb'), content_type='application/pdf')

    # -------------------------------------------------------------------
    # Caso nada funcione
    # -------------------------------------------------------------------
    messages.error(request, 'Não foi possível gerar ou localizar o certificado.')
    return redirect(f"{reverse('meus_eventos')}?evento={evento_id}")


# -------------------------------------------------------------------
# Detalhe público do evento
# -------------------------------------------------------------------
def detalhe_evento_publico(request, evento_id):
    evento = get_object_or_404(Evento, pk=evento_id)
    usuario = get_current_usuario(request)
    inscrito = evento.inscricaoevento_set.filter(inscrito=usuario).exists() if usuario else False
    return render(request, 'eventos/detalhe_evento_publico.html', {
        'evento': evento,
        'usuario': usuario,
        'inscrito': inscrito,
        'nav_items': nav_items
    })

# -------------------------------------------------------------------
# Galeria de fotos (visualização)
# -------------------------------------------------------------------
def galeria(request):
    """
    Exibe todos os eventos que possuem ao menos 1 imagem na galeria
    (ou thumb válida).
    """
    
    eventos_com_fotos = []

    for evento in Evento.objects.all().order_by('-data_inicio'):
            galeria_path = os.path.join(settings.MEDIA_ROOT, 'eventos', evento.get_gallery_name(), 'galeria')

            # Verifica se a galeria possui imagens
            if os.path.exists(galeria_path) and os.path.isdir(galeria_path):
                imagens = [f for f in os.listdir(galeria_path)
                        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
                if imagens:
                    eventos_com_fotos.append(evento)

    eventos = eventos_com_fotos  # só mostra eventos com fotos
    return render(request, 'eventos/galeria.html', {'eventos': eventos})

# -------------------------------------------------------------------
# Galeria de fotos de evento (upload + visualização + apagar)
# -------------------------------------------------------------------
def galeria_evento(request, evento_id):
    """
    Mostra a galeria de fotos do evento e permite upload e exclusão de fotos pelo organizador.
    SEM BANCO DE DADOS - usa apenas sistema de arquivos.
    """

    # Pega o usuário atual
    usuario = get_current_usuario(request)

    # Busca o evento ou retorna 404 se não existir
    evento = get_object_or_404(Evento, pk=evento_id)

    # Define o nome da pasta do evento com data e slug
    date_str = evento.data_inicio.strftime('%Y_%m_%d') if evento.data_inicio else 'no_date'
    event_dir_name = f"{date_str}_{slugify(evento.titulo)}"
    event_base = os.path.join(settings.MEDIA_ROOT, 'eventos', event_dir_name)

    # Caminho para a galeria de fotos
    galeria_dir = os.path.join(event_base, 'galeria')
    os.makedirs(galeria_dir, exist_ok=True)  # cria pasta galeria se não existir

    # Flag para informar se upload ocorreu
    upload_ok = False
    delete_ok = False

    # -------------------------------
    # Processa POST (upload ou delete)
    # -------------------------------
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Somente o organizador ou staff pode modificar fotos
        if not _is_event_owner(request, usuario, evento):
            messages.error(request, 'Acesso negado.')
            return redirect('galeria_evento', evento_id=evento.id)

        if action == 'upload':
            # UPLOAD DE FOTO
            file_obj = request.FILES.get('photo')
            if file_obj:
                # Caminho completo para salvar a foto
                save_path = os.path.join('eventos', event_dir_name, 'galeria', file_obj.name)
                full_path = os.path.join(settings.MEDIA_ROOT, save_path)
                
                # Salva o arquivo primeiro
                from django.core.files.storage import default_storage
                from django.core.files.base import ContentFile
                default_storage.save(save_path, ContentFile(file_obj.read()))
                
                # DEPOIS redimensiona a imagem
                try:
                    if os.path.exists(full_path):
                        from PIL import Image
                        with Image.open(full_path) as img:
                            # Converte para RGB se necessário
                            if img.mode in ('RGBA', 'P'):
                                img = img.convert('RGB')
                            
                            # Redimensiona mantendo proporção
                            img.thumbnail((600, 600), Image.Resampling.LANCZOS)
                            
                            # Salva substituindo o arquivo original
                            img.save(full_path, 'JPEG', quality=70, optimize=True)
                            print(f"Imagem redimensionada: {file_obj.name} -> {img.size}")
                except Exception as e:
                    print(f"Erro ao redimensionar {file_obj.name}: {e}")
                    # Continua mesmo com erro de redimensionamento
                
                upload_ok = True
                messages.success(request, 'Foto adicionada com sucesso!')
                try:
                    log_audit(request=request, usuario=usuario, action='upload_event_photo', object_type='Evento', object_id=evento.id, description=f'Foto enviada para galeria do evento {evento.id}: {file_obj.name}')
                except Exception:
                    pass
            else:
                messages.error(request, 'Nenhuma foto foi enviada.')

        elif action == 'delete':
            # EXCLUIR FOTO
            foto_path = request.POST.get('foto_path')
            if foto_path:
                full_path = os.path.join(settings.MEDIA_ROOT, foto_path)
                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                        delete_ok = True
                        messages.success(request, 'Foto apagada com sucesso!')
                        try:
                            log_audit(request=request, usuario=usuario, action='delete_event_photo', object_type='Evento', object_id=evento.id, description=f'Foto apagada: {foto_path}')
                        except Exception:
                            pass
                    except Exception as e:
                        messages.error(request, f'Erro ao apagar foto: {e}')
                else:
                    messages.error(request, 'Foto não encontrada.')
            else:
                messages.error(request, 'Caminho da foto não especificado.')

        return redirect('galeria_evento', evento_id=evento.id)

    # -------------------------------
    # Lista todas as fotos da galeria
    # -------------------------------
    fotos = []
    if os.path.exists(galeria_dir):
        # Lista arquivos que são imagens e cria estrutura com path completo
        for f in os.listdir(galeria_dir):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                fotos.append({
                    'path': f"eventos/{event_dir_name}/galeria/{f}",
                    'filename': f
                })

    # Renderiza template com informações da galeria
    return render(request, 'eventos/galeria_evento.html', {
        'evento': evento,
        'fotos': fotos,
        'usuario': usuario,
        'upload_ok': upload_ok,
        'delete_ok': delete_ok,
        'MEDIA_URL': settings.MEDIA_URL,
    })

# -------------------------------------------------------------------
# Inscrever e cancelar inscrição em eventos
# -------------------------------------------------------------------
@login_required
def inscrever_evento(request, evento_id):
    usuario = get_current_usuario(request)
    evento = get_object_or_404(Evento, pk=evento_id)

    # Restrição: apenas alunos e professores podem se inscrever
    if usuario.tipo.tipo.lower() not in ['aluno', 'professor']:
        messages.error(request, 'Apenas alunos e professores podem se inscrever em eventos.')
        return redirect('detalhe_evento', evento_id=evento.id)

    # Verifica limite de vagas
    if evento.quantidade_participantes and InscricaoEvento.objects.filter(evento=evento).count() >= evento.quantidade_participantes:
        messages.error(request, 'Número máximo de participantes atingido.')
        return redirect('detalhe_evento', evento_id=evento.id)

    # Cria ou recupera a inscrição existente
    inscr, created = InscricaoEvento.objects.get_or_create(inscrito=usuario, evento=evento)
    if created:
        messages.success(request, f'Inscrição no evento "{evento.titulo}" realizada com sucesso.')
        try:
            log_audit(request=request, usuario=usuario, action='create_inscription', object_type='InscricaoEvento', object_id=inscr.id, description=f'Inscrição criada no evento {evento.id}')
        except Exception:
            pass
    else:
        messages.info(request, f'Você já está inscrito no evento "{evento.titulo}".')

    return redirect('lista_eventos')

@login_required
def cancelar_inscricao(request, evento_id):
    usuario = get_current_usuario(request)
    evento = get_object_or_404(Evento, pk=evento_id)
    inscr = InscricaoEvento.objects.filter(inscrito=usuario, evento=evento).first()
    if inscr:
        inscr.delete()
        messages.success(request, f'Inscrição no evento "{evento.titulo}" cancelada.')
        try:
            log_audit(request=request, usuario=usuario, action='delete_inscription', object_type='InscricaoEvento', object_id=getattr(inscr, 'id', None), description=f'Inscrição cancelada no evento {evento.id}')
        except Exception:
            pass
    else:
        messages.info(request, 'Nenhuma inscrição encontrada para cancelar.')
    return redirect('lista_eventos')


# -------------------------------------------------------------------
# Debug JSON (somente staff)
# -------------------------------------------------------------------
@login_required
def debug_eventos(request, evento_id=None):
    if not getattr(request.user, 'is_staff', False):
        return HttpResponseForbidden('Acesso negado.')

    eventos = Evento.objects.all().order_by('-data_inicio')
    debug_list = []
    for e in eventos:
        debug_list.append({
            'id': e.id,
            'titulo': e.titulo,
            'criador': getattr(e.criador, 'nome_usuario', 'N/A'),
            'inscritos': e.inscricaoevento_set.count(),
            'finalizado': e.finalizado
        })
    try:
        log_audit(request=request, django_user=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None, action='api_query_events', object_type='Evento', description='Debug eventos JSON')
    except Exception:
        pass
    return JsonResponse({'eventos': debug_list})


@login_required
def auditoria(request):
    """Tela para superusuários Django consultarem logs de auditoria por data/usuário."""
    usuario = get_current_usuario(request)
    # Acesso restrito: somente superusuários Django podem acessar
    try:
        if not (request.user and request.user.is_authenticated and request.user.is_superuser):
            messages.error(request, 'Acesso negado: apenas superusuários podem consultar auditoria.')
            return redirect('meus_eventos')
    except Exception:
        messages.error(request, 'Acesso negado: credenciais inválidas para auditoria.')
        return redirect('meus_eventos')

    from usuarios.models import AuditLog
    from django.db.models import Q

    qs = AuditLog.objects.all().order_by('-timestamp')
    date_str = request.GET.get('date')
    username = request.GET.get('username', '').strip()
    
    if date_str:
        try:
            from django.utils.dateparse import parse_date
            d = parse_date(date_str)
            if d:
                qs = qs.filter(timestamp__date=d)
        except Exception:
            pass

    if username:
        try:
            # Filter by Usuario.nome_usuario or django_user.username
            qs = qs.filter(
                Q(usuario__nome_usuario__icontains=username) | 
                Q(django_user__username__icontains=username)
            )
        except Exception:
            pass

    # Get all unique usernames for autocomplete
    all_usuarios = Usuario.objects.values_list('nome_usuario', flat=True).distinct()
    all_django_users = User.objects.values_list('username', flat=True).distinct()
    all_usernames = sorted(set(list(all_usuarios) + list(all_django_users)))

    paginator = Paginator(qs, 50)
    page = request.GET.get('page', 1)
    try:
        logs = paginator.page(page)
    except Exception:
        logs = paginator.page(1)

    return render(request, 'eventos/auditoria.html', {
        'logs': logs,
        'usuario': usuario,
        'nav_items': nav_items,
        'all_usernames': all_usernames,
    })