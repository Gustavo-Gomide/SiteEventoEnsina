from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from usuarios.models import Usuario, TipoUsuario, Instituicao, AuditLog
import datetime
from eventos.models import Evento, TipoEvento

class AuditTests(TestCase):
    def setUp(self):
        self.client = Client()
        # cria tipos e usuarios
        self.tipo_org = TipoUsuario.objects.create(tipo='Organizador')
        self.instit = Instituicao.objects.create(nome='Uni Test')
        self.org_user = User.objects.create_user(username='org_audit', password='pass')
        self.org = Usuario.objects.create(nome='Org Audit', tipo=self.tipo_org, nome_usuario='org_audit', user=self.org_user)

    def test_creating_event_generates_auditlog(self):
        # cria evento diretamente (sinal post_save deve registrar)
        tipo_ev = TipoEvento.objects.create(tipo='Palestra')
        ev = Evento.objects.create(
            titulo='Evento Audit',
            tipo=tipo_ev,
            modalidade='online',
            data_inicio=datetime.date(2025,11,1),
            data_fim=datetime.date(2025,11,2),
            horario='10:00',
            criador=self.org,
        )

        # verifica se existe pelo menos um AuditLog relacionado
        exists = AuditLog.objects.filter(action__in=['create_event', 'update_event'], object_type='Evento', object_id=str(ev.id)).exists()
        self.assertTrue(exists, 'Esperava AuditLog para criação de Evento')

    def test_debug_api_generates_auditlog(self):
        # cria um evento para debug endpoint
        tipo_ev = TipoEvento.objects.create(tipo='Curso')
        ev = Evento.objects.create(
            titulo='Evento Debug',
            tipo=tipo_ev,
            modalidade='online',
            data_inicio=datetime.date(2025,11,1),
            data_fim=datetime.date(2025,11,2),
            horario='10:00',
            criador=self.org,
        )

        # cria user staff para acessar endpoint debug
        staff = User.objects.create_user(username='staff1', password='pass')
        staff.is_staff = True
        staff.save()
        self.client.login(username='staff1', password='pass')

        url = reverse('debug_evento', args=[ev.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # verifica AuditLog com action api_query_events ou debug
        found = AuditLog.objects.filter(action__icontains='api_query', object_type='Evento').exists()
        self.assertTrue(found, 'Esperava AuditLog para consulta API de eventos')
