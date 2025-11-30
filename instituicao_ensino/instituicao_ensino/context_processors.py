from django.urls import reverse
from usuarios.models import Usuario


def global_nav(request):
    """Context processor que injeta duas listas: nav_left e nav_right, e current_usuario.

    Usar reverse() evita hardcoding e erros de rota.
    """
    usuario = None
    if request.user.is_authenticated:
        try:
            usuario = Usuario.objects.get(user=request.user)
        except Usuario.DoesNotExist:
            # fallback para session legacy
            usuario_id = request.session.get('usuario_id')
            if usuario_id:
                try:
                    usuario = Usuario.objects.get(pk=usuario_id)
                except Usuario.DoesNotExist:
                    usuario = None
    else:
        usuario_id = request.session.get('usuario_id')
        if usuario_id:
            try:
                usuario = Usuario.objects.get(pk=usuario_id)
            except Usuario.DoesNotExist:
                usuario = None

    # left: sempre visíveis
    nav_left = [
        {'label': 'Home', 'url': reverse('main')},
        {'label': 'Galeria', 'url': reverse('galeria')},
        {'label': 'Eventos', 'url': reverse('lista_eventos_root')},
    ]

    nav_right = []
    if usuario:
        # Acesso rápido a 'Meus Eventos' para qualquer usuário autenticado
        nav_right.append({'label': 'Meus Eventos', 'url': reverse('meus_eventos')})
        nav_right.append({'label': 'Perfil', 'url': reverse('perfil')})
        # somente usuários com username 'admin' veem a auditoria
        if usuario.tipo.tipo in ['Professor', 'Organizador', 'Funcionario']:
            nav_right.append({'label': 'Criar Evento', 'url': reverse('criar_evento')})

        try:
            if request.user and request.user.is_authenticated and getattr(request.user, 'username', '') == 'admin':
                nav_right.append({'label': 'Auditoria', 'url': reverse('auditoria_eventos')})
        except Exception:
            # em caso de qualquer erro ao acessar request.user, não mostrar o link
            pass
        nav_right.append({'label': 'Logout', 'url': reverse('logout')})
    else:
        nav_right.append({'label': 'Login', 'url': reverse('login')})
        nav_right.append({'label': 'Cadastro', 'url': reverse('cadastro')})

    return {'nav_left': nav_left, 'nav_right': nav_right, 'current_usuario': usuario}
