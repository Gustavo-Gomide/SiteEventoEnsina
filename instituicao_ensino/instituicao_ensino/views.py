from django.shortcuts import render
from eventos.models import Evento
from datetime import date
from usuarios.models import Usuario  # importa o modelo correto

nav_items = [
    {'label': 'Home', 'url': '/'},
    {'label': 'Login', 'url': '/login/'},
    {'label': 'Cadastro', 'url': '/cadastro/'},
    {'label': 'Criar Evento', 'url': '/eventos/criar/'},
    {'label': 'Eventos', 'url': '/eventos/'},
]

def main(request):

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

    # Evita erro de tipo incorreto
    if request.user.is_authenticated and isinstance(request.user, Usuario):
        ativos = ativos.exclude(criador=request.user)
        destaques = destaques.exclude(criador=request.user)

    context = {
        'nav_items': nav_items,
        'destaques': destaques,
        'ativos': ativos,
    }

    return render(request, 'main.html', context)
