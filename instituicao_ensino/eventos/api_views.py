from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import SimpleRateThrottle
from .models import Evento, InscricaoEvento
from .serializers import EventoSerializer, InscricaoCreateSerializer
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny


class EventListThrottle(SimpleRateThrottle):
    scope = 'event_list'

    def get_cache_key(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return None
        return self.cache_format % {
            'scope': self.scope,
            'ident': request.user.pk
        }


class EventRegisterThrottle(SimpleRateThrottle):
    scope = 'event_register'

    def get_cache_key(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return None
        return self.cache_format % {
            'scope': self.scope,
            'ident': request.user.pk
        }


class EventoListAPIView(generics.ListAPIView):
    """Listagem de eventos disponíveis."""
    queryset = Evento.objects.all().order_by('data_inicio')
    serializer_class = EventoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [EventListThrottle]


class InscricaoAPIView(APIView):
    """Permite que usuário autenticado se inscreva em um evento via POST.

    Payload: { "evento_id": <id> }
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [EventRegisterThrottle]

    def post(self, request, *args, **kwargs):
        serializer = InscricaoCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        evento_id = serializer.validated_data['evento_id']
        evento = get_object_or_404(Evento, pk=evento_id)

        # find Perfil (Usuario) linked to Django user
        try:
            perfil = request.user.profile
        except Exception:
            return Response({'detail': 'Perfil do usuário não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

        # Only allow users with TipoUsuario 'Aluno' or 'Professor'
        tipo_nome = getattr(getattr(perfil, 'tipo', None), 'tipo', '') or ''
        if tipo_nome.lower() not in ('aluno', 'professor'):
            return Response({'detail': 'Apenas alunos ou professores podem se inscrever.'}, status=status.HTTP_403_FORBIDDEN)

        # Prevent event creator from registering
        try:
            if evento.criador and perfil.pk == evento.criador.pk:
                return Response({'detail': 'Criador do evento não pode se inscrever.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            pass

        # Prevent Django superusers from registering via API
        if getattr(request.user, 'is_superuser', False):
            return Response({'detail': 'Superusuário não pode se inscrever.'}, status=status.HTTP_403_FORBIDDEN)

        # prevent duplicate inscriptions
        if InscricaoEvento.objects.filter(evento=evento, inscrito=perfil).exists():
            return Response({'detail': 'Usuário já inscrito neste evento.'}, status=status.HTTP_400_BAD_REQUEST)

        # check capacity unless sem_limites
        if (evento.quantidade_participantes and not evento.sem_limites):
            current = InscricaoEvento.objects.filter(evento=evento).count()
            if evento.quantidade_participantes is not None and current >= evento.quantidade_participantes:
                return Response({'detail': 'Evento atingiu o número máximo de participantes.'}, status=status.HTTP_400_BAD_REQUEST)

        inscricao = InscricaoEvento.objects.create(evento=evento, inscrito=perfil)
        return Response(serializer.to_representation(inscricao), status=status.HTTP_201_CREATED)


# Public token obtain endpoint (AllowAny) — not subject to global IsAuthenticated
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def api_obtain_auth_token(request):
    serializer = AuthTokenSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    token, created = Token.objects.get_or_create(user=user)
    return Response({'token': token.key})
