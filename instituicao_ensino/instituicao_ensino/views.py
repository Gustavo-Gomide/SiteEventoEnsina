from django.shortcuts import render
from eventos.models import Evento, InscricaoEvento
from datetime import date
from usuarios.models import Usuario
from django.contrib.auth import get_user_model

nav_items = [
    {'label': 'Home', 'url': '/'},
    {'label': 'Login', 'url': '/login/'},
    {'label': 'Cadastro', 'url': '/cadastro/'},
    {'label': 'Criar Evento', 'url': '/eventos/criar/'},
    {'label': 'Eventos', 'url': '/eventos/'},
]

def main(request):
    # Inicializa as variáveis
    current_usuario = None
    inscricoes_usuario = []

    # Verifica o usuário logado
    if request.user.is_authenticated:
        try:
            # Busca o Usuario através do relacionamento 'profile'
            if hasattr(request.user, 'profile'):
                current_usuario = request.user.profile
            
            # Busca as inscrições do usuário
            if current_usuario:
                inscricoes_usuario = list(InscricaoEvento.objects.filter(
                    inscrito=current_usuario
                ).values_list('evento_id', flat=True))
            
        except Exception as e:
            print(f"DEBUG - Erro ao processar usuário: {e}")

    # Busca os eventos (SEM excluir os do usuário atual)
    destaques = Evento.objects.filter(
        finalizado=False,
    ).exclude(thumb='').order_by('data_inicio')[:5]

    if not destaques.exists():
        destaques = Evento.objects.filter(
            finalizado=False,
        ).order_by('data_inicio')[:3]

    ativos = Evento.objects.filter(
        finalizado=False,
    ).order_by('data_inicio')

    context = {
        'nav_items': nav_items,
        'destaques': destaques,
        'ativos': ativos,
        'current_usuario': current_usuario,
        'inscricoes_usuario': inscricoes_usuario,
    }

    return render(request, 'main.html', context)

def politica_privacidade(request):
    return render(request, 'politica_privacidade.html', {'nav_items': nav_items})

def termos_uso(request):
    return render(request, 'termos_uso.html', {'nav_items': nav_items})