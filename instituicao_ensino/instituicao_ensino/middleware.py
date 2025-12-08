
"""
Middleware customizado para registrar auditoria de consultas API que retornam JSON.
"""

from django.http import JsonResponse
from usuarios.utils import log_audit



class AuditMiddleware:
    """
    Middleware que registra auditoria de consultas API que retornam JsonResponse.

    Regras:
    - Se a resposta for JsonResponse e o path contiver 'eventos' ou '/api/', registra a consulta.
    - Apenas adiciona um registro com método GET e parâmetros.
    - Nunca interrompe a requisição por falha de auditoria.
    """
    def __init__(self, get_response):
        """
        Inicializa o middleware com a função get_response.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Intercepta a requisição e registra auditoria se for uma resposta JSON de eventos ou API.
        """
        response = self.get_response(request)

        try:
            if isinstance(response, JsonResponse):
                path = request.path.lower()
                if 'eventos' in path or '/api/' in path:
                    user = None
                    django_user = getattr(request, 'user', None) if getattr(request, 'user', None) and request.user.is_authenticated else None
                    # Evita import cycles: log_audit resolve model lazy
                    log_audit(
                        request=request,
                        django_user=django_user,
                        action='api_query_events',
                        object_type='Evento',
                        object_id=None,
                        description=f'API query: {request.path}?{request.META.get("QUERY_STRING", "")}'
                    )
        except Exception:
            # Nunca falha a requisição por erro de auditoria
            pass

        return response
