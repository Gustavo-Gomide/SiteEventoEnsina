"""
URL configuration for instituicao_ensino project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import main

from django.conf.urls import handler404
from django.shortcuts import redirect
from django.contrib import messages

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", main, name='main'),
    path('usuarios/', include('usuarios.urls')),
    path('eventos/', include('eventos.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


from django.views.static import serve

if settings.DEBUG is False:
    # apenas para testes locais, NÃO usar em produção
    urlpatterns += [
        path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    ]

def custom_400(request, exception):
    messages.info(request, "Requisição inválida (400).")
    return redirect('main')

def custom_403(request, exception):
    messages.info(request, "Acesso negado (403).")
    return redirect('main')

def custom_404(request, exception):
    messages.info(request, "A página que você tentou acessar não existe (404).")
    return redirect('main')

def custom_500(request):
    messages.info(request, "Ocorreu um erro interno no servidor ou parâmetro informado inválido (500).")
    return redirect('main')

handler400 = custom_400
handler403 = custom_403
handler404 = custom_404
handler500 = custom_500