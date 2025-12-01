from django.http import JsonResponse
from usuarios.utils import log_audit


class AuditMiddleware:
    """Middleware simples que registra consultas via API (respostas JSON)

    Regras:
    - Se a resposta for JsonResponse e o path contiver 'eventos' ou '/api/', registra a consulta.
    - Apenas adiciona um registro com método GET e parâmetros.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            if isinstance(response, JsonResponse):
                path = request.path.lower()
                if 'eventos' in path or '/api/' in path:
                    user = None
                    django_user = getattr(request, 'user', None) if getattr(request, 'user', None) and request.user.is_authenticated else None
                    # avoid import cycles: log_audit will resolve model lazily
                    log_audit(request=request, django_user=django_user, action='api_query_events', object_type='Evento', object_id=None, description=f'API query: {request.path}?{request.META.get("QUERY_STRING", "")}')
        except Exception:
            # never fail the request due to audit
            pass

        return response
