from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from usuarios.models import Usuario, TipoUsuario, Instituicao, Perfil, Certificado
from eventos.models import Evento, TipoEvento, InscricaoEvento
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
import io
import datetime


class EventFlowTests(TestCase):
    """
    Testes de integração para fluxo principal de eventos:
    - Criação de usuários, tipos e eventos
    - Inscrição de alunos
    - Finalização de evento e geração de certificados
    - Download de certificados
    """

    def setUp(self):
        """
        Executado antes de cada teste.
        - Cria tipos de usuário (Aluno e Organizador)
        - Cria instituição de teste
        - Cria usuários Django e vincula ao modelo Usuario
        - Cria perfil para cada usuário
        - Cria um tipo de evento e um evento de teste
        - Inicializa o Client de testes
        """
        # criar tipos de usuários
        self.tipo_aluno = TipoUsuario.objects.create(tipo='Aluno')
        self.tipo_org = TipoUsuario.objects.create(tipo='Organizador')
        self.instit = Instituicao.objects.create(nome='Uni Test')

        # criar usuários Django
        self.org_user = User.objects.create_user(username='org1', password='pass')
        self.aluno_user = User.objects.create_user(username='aluno1', password='pass')

        # criar registros do modelo Usuario vinculando aos usuários Django
        self.org = Usuario.objects.create(
            nome='Organizador',
            tipo=self.tipo_org,
            nome_usuario='org1',
            user=self.org_user
        )
        self.aluno = Usuario.objects.create(
            nome='Aluno',
            tipo=self.tipo_aluno,
            nome_usuario='aluno1',
            user=self.aluno_user
        )

        # criar perfis (para foto, etc)
        Perfil.objects.get_or_create(usuario=self.org)
        Perfil.objects.get_or_create(usuario=self.aluno)

        # criar tipo de evento e evento
        self.tipo_ev = TipoEvento.objects.create(tipo='Curso')
        self.evento = Evento.objects.create(
            titulo='Teste Evento',
            tipo=self.tipo_ev,
            modalidade='online',
            data_inicio=datetime.date(2025, 10, 1),
            data_fim=datetime.date(2025, 10, 2),
            horario=datetime.time(10, 0),
            quantidade_participantes=10,
            organizador='org1',
            criador=self.org,
        )

        # inicializa Client para requisições de teste
        self.client = Client()

    def test_inscricao_flow(self):
        """
        Testa o fluxo de inscrição:
        - login do aluno
        - post para inscrever no evento
        - verifica se inscrição foi criada
        """
        # login do aluno
        logged = self.client.login(username='aluno1', password='pass')
        self.assertTrue(logged)

        # envia POST para endpoint de inscrição
        url = reverse('inscrever_evento', args=[self.evento.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)  # deve redirecionar após inscrição

        # verifica se inscrição existe no banco
        self.assertTrue(
            InscricaoEvento.objects.filter(evento=self.evento, inscrito=self.aluno).exists()
        )

    @patch('usuarios.generator.generate_certificates_for_event')
    def test_finalizar_calls_generate(self, mock_call):
        """
        Testa o endpoint de finalizar evento:
        - cria inscrição validada
        - login do organizador
        - envia POST para finalizar
        - verifica se comando de gerar certificados foi chamado
        """
        # cria inscrição já validada
        InscricaoEvento.objects.create(evento=self.evento, inscrito=self.aluno, is_validated=True)

        # login do organizador
        self.client.login(username='org1', password='pass')
        url = reverse('finalizar_evento', args=[self.evento.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)

        # verifica se a função generate_certificates_for_event foi chamada
        mock_call.assert_called_with(self.evento.id)

    def test_pegar_certificado_redirects_to_pdf(self):
        """
        Testa o fluxo de pegar certificado:
        - cria um certificado com PDF
        - login do aluno
        - verifica se o acesso redireciona corretamente para o arquivo PDF
        """
        # cria certificado com arquivo PDF fictício
        pdf_content = SimpleUploadedFile(
            'test.pdf',
            b'%PDF-1.4 test',
            content_type='application/pdf'
        )
        cert = Certificado.objects.create(
            usuario=self.aluno,
            evento=self.evento,
            nome='Teste',
            pdf=pdf_content
        )

        # login do aluno e request para pegar_certificado
        self.client.login(username='aluno1', password='pass')
        url = reverse('pegar_certificado', args=[self.evento.id])
        resp = self.client.get(url)

        # deve redirecionar para media file (status 302)
        self.assertEqual(resp.status_code, 302)
