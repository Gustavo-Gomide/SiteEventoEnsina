from django.urls import path
from . import views

urlpatterns = [
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_usuario, name='logout'),
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/inscritos/<int:evento_id>/', views.lista_inscritos_evento, name='lista_inscritos_evento'),
    # Public profile URLs
    path('u/<str:nome_usuario>/', views.perfil_publico, name='perfil_publico'),
    path('certificado/<str:public_id>/', views.certificado_publico, name='certificado_publico'),
    path('instituicao/<int:instituicao_id>/', views.instituicao_publica, name='instituicao_publica'),
    path('u/<str:nome_usuario>/certificados/', views.perfil_certificados, name='perfil_certificados'),
    path('reconcile/', views.reconcile_users, name='reconcile_users'),
]
