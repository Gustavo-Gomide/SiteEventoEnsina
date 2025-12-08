
"""
Serializers para conversão e validação de dados dos modelos Evento e InscricaoEvento.

Inclui validações customizadas e métodos de representação para uso nas APIs.
"""

from rest_framework import serializers
from .models import Evento, InscricaoEvento



class EventoSerializer(serializers.ModelSerializer):
    """
    Serializador para o modelo Evento.
    Converte instâncias de Evento para JSON e vice-versa, para uso em APIs.
    """
    class Meta:
        model = Evento
        fields = [
            'id',
            'titulo',
            'data_inicio',
            'data_fim',
            'horario',
            'local',
            'link',
            'organizador',
            'modalidade',
            'quantidade_participantes',
            'sem_limites',
        ]



class InscricaoCreateSerializer(serializers.Serializer):
    """
    Serializador para criação de inscrições em eventos.
    Valida o ID do evento, cria a inscrição e define a representação de saída.
    """
    evento_id = serializers.IntegerField()

    def validate_evento_id(self, value):
        """
        Valida se o evento informado existe.
        """
        try:
            evento = Evento.objects.get(pk=value)
        except Evento.DoesNotExist:
            raise serializers.ValidationError('Evento não encontrado.')
        return value

    def create(self, validated_data):
        """
        Cria uma nova inscrição para o usuário autenticado no evento informado.
        """
        usuario = self.context['request'].user
        # Mapeia o usuário Django para o perfil Usuario
        try:
            perfil = usuario.profile
        except Exception:
            perfil = None

        evento = Evento.objects.get(pk=validated_data['evento_id'])
        inscricao = InscricaoEvento.objects.create(evento=evento, inscrito=perfil)
        return inscricao

    def to_representation(self, instance):
        """
        Define a estrutura de saída da inscrição criada.
        """
        return {
            'id': instance.id,
            'evento': instance.evento.id,
            'inscrito': instance.inscrito.nome_usuario if instance.inscrito else None,
            'data_inscricao': instance.data_inscricao,
            'is_validated': instance.is_validated,
        }
