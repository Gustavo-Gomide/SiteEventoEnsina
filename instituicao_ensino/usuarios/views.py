"""
Users views and helpers.

This module provides UI views for user registration, login, profile
management and a helper `get_current_usuario()` which bridges the legacy
session-based `usuario_id` approach with Django's `User` authentication.

Important notes:
- When a Django `User` logs in, we try to link a `Usuario` with the same
    `nome_usuario`. This keeps older code working while allowing gradual
    migration to Django's auth system.
- The `perfil` view ensures per-user media directories exist before saving
    files by calling `create_user_dirs()`.
"""

from django.shortcuts import render, redirect, get_object_or_404
from .forms import CadastroUsuarioForm, LoginForm, PerfilForm, UsuarioEditForm
from .models import Usuario, Perfil, Certificado, Instituicao, TipoUsuario
from instituicao_ensino.views import nav_items
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse
import csv

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.shortcuts import Http404


def cadastro(request):
    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cadastro realizado com sucesso. Faça login.')
            return redirect('login')
    else:
        form = CadastroUsuarioForm()
    return render(request, 'cadastro.html', {'form': form, 'nav_items': nav_items})


def login_usuario(request):
    mensagem = ''
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            nome_usuario = form.cleaned_data['nome_usuario']
            senha = form.cleaned_data['senha']
            # usar autenticação do Django
            user = authenticate(request, username=nome_usuario, password=senha)
            if user is not None:
                auth_login(request, user)
                # vincular também na session legacy para compatibilidade
                try:
                    perfil = Usuario.objects.get(nome_usuario=nome_usuario)
                    # garantir link com User do Django
                    if not perfil.user:
                        perfil.user = user
                        perfil.save()
                    request.session['usuario_id'] = perfil.id
                except Usuario.DoesNotExist:
                    pass
                messages.success(request, f'Bem-vindo, {user.username}!')
                return redirect('lista_eventos')
            else:
                mensagem = 'Usuário ou senha inválidos'
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form, 'mensagem': mensagem, 'nav_items': nav_items})


def logout_usuario(request):
    # logout do Django e remover session legacy
    auth_logout(request)
    request.session.pop('usuario_id', None)
    messages.info(request, 'Você saiu da sessão.')
    return redirect('login')


def get_current_usuario(request):
    # prefer Django user if autenticado
    if request.user.is_authenticated:
        try:
            return Usuario.objects.get(user=request.user)
        except Usuario.DoesNotExist:
            # Try to find a Usuario by matching the Django username and link it
            try:
                perfil = Usuario.objects.get(nome_usuario=request.user.username)
                perfil.user = request.user
                perfil.save()
                # also set legacy session for other code paths
                request.session['usuario_id'] = perfil.id
                return perfil
            except Usuario.DoesNotExist:
                # fallback para session legacy
                # As a convenience, create a minimal Usuario for this Django User so
                # they can immediately edit a profile via the web UI. This keeps the
                # application usable even before a full migration to AUTH_USER_MODEL.
                try:
                    from .utils import create_user_dirs
                    tipo, _ = TipoUsuario.objects.get_or_create(tipo='Aluno')
                    inst = None
                    novo = Usuario.objects.create(
                        nome=request.user.get_full_name() or request.user.username,
                        tipo=tipo,
                        instituicao=inst,
                        telefone='',
                        nome_usuario=request.user.username,
                        email=request.user.email,
                        user=request.user,
                    )
                    try:
                        create_user_dirs(novo)
                    except Exception:
                        pass
                    request.session['usuario_id'] = novo.id
                    return novo
                except Exception:
                    pass
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return None
    try:
        return Usuario.objects.get(pk=usuario_id)
    except Usuario.DoesNotExist:
        return None


def usuario_login_required(view_func):
    """Decorator that accepts either a linked Django user or a legacy session 'usuario_id'.

    Many views historically relied on `request.session['usuario_id']`. This decorator
    checks `get_current_usuario(request)` and only redirects to the login page if
    no Usuario is available. It preserves compatibility with Django's @login_required
    while supporting older session-based flows.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        usuario = get_current_usuario(request)
        if usuario is None:
            # fall back to Django login_required behaviour
            if not request.user.is_authenticated:
                return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped


@usuario_login_required
def perfil(request):
    usuario = get_current_usuario(request)
    # If we couldn't resolve a Usuario, guide the user to create one.
    if usuario is None:
        if request.user.is_authenticated:
            messages.info(request, 'Nenhum perfil de aplicativo encontrado para sua conta Django. Por favor, complete o cadastro.')
            return redirect('cadastro')
        else:
            return redirect('login')

    perfil_obj, _ = Perfil.objects.get_or_create(usuario=usuario)

    if request.method == 'POST':
        uform = UsuarioEditForm(request.POST, instance=usuario)
        pform = PerfilForm(request.POST, request.FILES, instance=perfil_obj)
        if uform.is_valid() and pform.is_valid():
            # ensure user dirs exist before saving files
            from .utils import create_user_dirs
            created = False
            try:
                created = create_user_dirs(usuario)
            except Exception:
                created = False
            if not created:
                messages.warning(request, 'Atenção: não foi possível criar diretórios de usuário no servidor. Verifique permissões ou contate o administrador.')
            uform.save()
            # save profile fields (biografia, mostrar flags, foto)
            try:
                perfil = pform.save()
            except Exception as e:
                # log and show message if saving profile files failed
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Erro ao salvar perfil para usuario {getattr(usuario, "id", None)}: {e}')
                messages.error(request, 'Erro ao salvar perfil (problema com upload de arquivo?). Verifique os arquivos e tente novamente.')
                # re-render form with errors
                return render(request, 'perfil.html', {'usuario': usuario, 'uform': uform, 'pform': pform, 'nav_items': nav_items})
            # ensure we show the persisted data
            try:
                usuario.refresh_from_db()
                perfil_obj.refresh_from_db()
            except Exception:
                pass
            messages.success(request, 'Perfil atualizado com sucesso.')
            return redirect('perfil')
    else:
        uform = UsuarioEditForm(instance=usuario)
        pform = PerfilForm(instance=perfil_obj)

    # helpful logging for debugging profile updates and surface form errors
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f'perfil view: usuario={getattr(usuario, "id", None)} chamada method={request.method}')
    if request.method == 'POST' and (not uform.is_valid() or not pform.is_valid()):
        # log errors for developers
        logger.debug(f'Perfil form errors: uform={uform.errors.as_json()} pform={pform.errors.as_json()}')
        # send user-friendly messages for each form error so the UI shows them
        for field, errors in uform.errors.items():
            for e in errors:
                messages.error(request, f'Erro no campo do usuário "{field}": {e}')
        for field, errors in pform.errors.items():
            for e in errors:
                messages.error(request, f'Erro no campo do perfil "{field}": {e}')
    
    # extrai apenas os dígitos do telefone e isola o número local (sem país/DDD)
    import re as _re
    tel_digits = _re.sub(r'\D', '', usuario.telefone or '')
    # pega sempre os últimos 11 dígitos (DDD + número local) e então o último 9 dígitos
    if len(tel_digits) >= 11:
        core = tel_digits[-11:]
    else:
        core = tel_digits
    local = core[-9:]

    return render(request, 'perfil.html', {'usuario': usuario, 'uform': uform, 'pform': pform, 'nav_items': nav_items, 'telefone': local})





@login_required
def lista_inscritos_evento(request, evento_id):
    # Apenas professores/organizadores podem ver inscritos
    usuario = get_current_usuario(request)
    if not usuario or usuario.tipo.tipo not in ['Professor', 'Organizador', 'Funcionario']:
        return HttpResponseForbidden('Acesso negado')

    from eventos.models import Evento
    evento = get_object_or_404(Evento, pk=evento_id)
    # Recupera inscrições com dados de instituição
    inscritos = evento.inscricaoevento_set.select_related('aluno__instituicao', 'aluno')

    # Se o usuário quiser exportar CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="inscritos_evento_{evento.id}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Nome', 'Usuario', 'Instituicao', 'Telefone', 'Data Inscricao'])
        for i in inscritos:
            aluno = i.aluno
            inst = aluno.instituicao.nome if aluno.instituicao else ''
            writer.writerow([aluno.nome, aluno.nome_usuario, inst, aluno.telefone, i.data_inscricao])
        return response

    return render(request, 'inscritos_evento.html', {'evento': evento, 'inscritos': inscritos, 'nav_items': nav_items, 'usuario': usuario})


def perfil_publico(request, nome_usuario):
    """Mostra o perfil público de um usuário por `nome_usuario`."""
    try:
        usuario = Usuario.objects.select_related('instituicao').get(nome_usuario=nome_usuario)
    except Usuario.DoesNotExist:
        raise Http404('Usuário não encontrado')

    # garantir que exista um objeto Perfil (para foto/biografia)
    perfil_obj, _ = Perfil.objects.get_or_create(usuario=usuario)
    return render(request, 'perfil_publico.html', {'usuario': usuario, 'perfil': perfil_obj, 'nav_items': nav_items})


def instituicao_publica(request, instituicao_id):
    """Página pública para instituições."""
    try:
        inst = Instituicao.objects.get(pk=instituicao_id)
    except Instituicao.DoesNotExist:
        raise Http404('Instituição não encontrada')

    # listar usuários públicos desta instituição (opcional)
    usuarios = Usuario.objects.filter(instituicao=inst)[:50]
    return render(request, 'instituicao_publica.html', {'instituicao': inst, 'usuarios': usuarios, 'nav_items': nav_items})


def perfil_certificados(request, nome_usuario):
    """Lista todos os certificados públicos de um usuário (acessível por qualquer visitante)."""
    try:
        usuario = Usuario.objects.get(nome_usuario=nome_usuario)
    except Usuario.DoesNotExist:
        raise Http404('Usuário não encontrado')

    certificados = Certificado.objects.filter(usuario=usuario).order_by('-data_emitido')
    evento_id = request.GET.get('evento')
    if evento_id:
        certificados = certificados.filter(evento__id=int(evento_id))
    return render(request, 'certificates_list.html', {'usuario': usuario, 'certificados': certificados, 'nav_items': nav_items})


def certificado_publico(request, public_id):
    """Mostra um certificado público para verificação via QR.

    Busca o Certificado pelo `public_id` e exibe metadados e o arquivo
    (HTML, PDF ou PNG) se disponível.
    """
    from .models import Certificado
    try:
        cert = Certificado.objects.select_related('usuario', 'evento').get(public_id=public_id)
    except Certificado.DoesNotExist:
        raise Http404('Certificado não encontrado')

    # prefer binary files if available
    file_url = None
    if cert.pdf:
        file_url = cert.pdf.url
    elif cert.png:
        file_url = cert.png.url
    elif cert.arquivo:
        file_url = cert.arquivo.url

    return render(request, 'certificado_publico.html', {'cert': cert, 'file_url': file_url, 'nav_items': nav_items})


@login_required
def reconcile_users(request):
    """Staff-only view: attempt to link Django User objects to Usuario by matching username.

    This is a convenience endpoint to fix records where the one-to-one wasn't set.
    """
    if not (request.user.is_authenticated and getattr(request.user, 'is_staff', False)):
        return HttpResponseForbidden('Acesso negado')

    linked = 0
    from django.contrib.auth import get_user_model
    User = get_user_model()
    for u in User.objects.all():
        try:
            perfil = Usuario.objects.get(nome_usuario=u.username)
            if not perfil.user:
                perfil.user = u
                perfil.save()
                linked += 1
        except Usuario.DoesNotExist:
            continue

    return render(request, 'reconcile_result.html', {'linked': linked, 'nav_items': nav_items})
