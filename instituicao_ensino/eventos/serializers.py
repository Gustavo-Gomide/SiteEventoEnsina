from rest_framework import serializers
from .models import Evento, InscricaoEvento


class EventoSerializer(serializers.ModelSerializer):
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
    evento_id = serializers.IntegerField()

    def validate_evento_id(self, value):
        try:
            evento = Evento.objects.get(pk=value)
        except Evento.DoesNotExist:
            raise serializers.ValidationError('Evento não encontrado.')
        return value

    def create(self, validated_data):
        usuario = self.context['request'].user
        # map Django user to Usuario profile
        try:
            perfil = usuario.profile
        except Exception:
            perfil = None

        evento = Evento.objects.get(pk=validated_data['evento_id'])
        inscricao = InscricaoEvento.objects.create(evento=evento, inscrito=perfil)
        return inscricao

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'evento': instance.evento.id,
            'inscrito': instance.inscrito.nome_usuario if instance.inscrito else None,
            'data_inscricao': instance.data_inscricao,
            'is_validated': instance.is_validated,
        }
