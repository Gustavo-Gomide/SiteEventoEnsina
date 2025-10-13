from django.urls import path
from . import views  # importa todas as views do app 'eventos'

urlpatterns = [
    # Página inicial do app: lista resumida de eventos (root do app)
    path('', views.lista_eventos, name='lista_eventos_root'),

    # Criação de evento (somente para organizadores)
    path('criar/', views.criar_evento, name='criar_evento'),

    # Lista completa de eventos disponíveis
    path('lista/', views.lista_eventos, name='lista_eventos'),

    # Página do usuário mostrando seus eventos e inscrições
    path('meus/', views.meus_eventos, name='meus_eventos'),

    # Detalhes de um evento específico (id passado como inteiro)
    # Corrigido: view correta é 'detalhes_evento' (com 's')
    path('detalhe/<int:evento_id>/', views.detalhe_evento_publico, name='detalhe_evento'),

    # Inscrição em evento (POST via aluno)
    path('inscrever/<int:evento_id>/', views.inscrever_evento, name='inscrever_evento'),

    # Cancelamento de inscrição em evento
    path('cancelar/<int:evento_id>/', views.cancelar_inscricao, name='cancelar_inscricao'),

    # Galeria geral de eventos (thumbnails)
    path('galeria/', views.galeria, name='galeria'),

    # Gerenciamento do evento (somente para organizador)
    path('gerenciar/<int:evento_id>/', views.gerenciar_evento, name='gerenciar_evento'),

    # Finalização de evento (marca como finalizado e publica certificados)
    path('finalizar/<int:evento_id>/', views.finalizar_evento, name='finalizar_evento'),

    # Pegar certificado (download) de um evento
    path('pegar/<int:evento_id>/', views.pegar_certificado, name='pegar_certificado'),

    # Galeria de fotos de um evento específico
    path('galeria/<int:evento_id>/', views.galeria_evento, name='galeria_evento'),

    # Endpoint de debug para informações do evento (somente desenvolvimento)
    path('debug/<int:evento_id>/', views.debug_eventos, name='debug_evento'),
]
