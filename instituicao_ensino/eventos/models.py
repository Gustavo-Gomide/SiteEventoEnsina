
"""
Modelos de dados para gerenciamento de eventos, tipos de eventos e inscrições.

Inclui validações, manipulação de arquivos de imagem, geração de pastas e métodos utilitários para o sistema de eventos.
"""

import os
from django.db import models
from django.conf import settings
from django.db import models as dj_models
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image
from django.utils.text import slugify
from .utils import resize_image


# ============================================================
# MODELO: TipoEvento
# ============================================================

class TipoEvento(models.Model):
    """
    Modelo para armazenar os tipos de eventos disponíveis (Ex: Palestra, Oficina, Curso).

    Campos:
        tipo (CharField): Nome do tipo de evento, único.
    """
    tipo = models.CharField(max_length=50, unique=True)

    def __str__(self):
        """
        Retorna o nome do tipo de evento para exibição.
        """
        return self.tipo


# ============================================================
# MODELO: Evento
# ============================================================

class Evento(models.Model):
    """
    Modelo que representa um evento no sistema.

    Campos:
        titulo (CharField): Título do evento.
        tipo (ForeignKey): Tipo do evento (relacionado a TipoEvento).
        modalidade (CharField): Modalidade do evento (online, presencial, híbrido).
        data_inicio (DateField): Data de início do evento.
        data_fim (DateField): Data de término do evento.
        horario (TimeField): Horário de início do evento.
        local (CharField): Local do evento (opcional).
        link (URLField): Link do evento (opcional).
        quantidade_participantes (PositiveIntegerField): Limite de participantes (opcional).
        sem_limites (BooleanField): Indica se o evento não tem limite de participantes.
        organizador (CharField): Nome do organizador (opcional).
        criador (ForeignKey): Usuário criador do evento.
        thumb (ImageField): Imagem principal do evento.
        descricao (TextField): Descrição do evento.
        horas (DecimalField): Carga horária do evento.
        gallery_slug (CharField): Slug para galeria de imagens.
        finalizado (BooleanField): Indica se o evento foi finalizado.
    """

    MODALIDADES = [
        ('online', 'Online'),
        ('presencial', 'Presencial'),
        ('hibrido', 'Híbrido'),
    ]

    titulo = models.CharField(max_length=200)
    tipo = models.ForeignKey(TipoEvento, on_delete=models.CASCADE)
    modalidade = models.CharField(max_length=10, choices=MODALIDADES)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    horario = models.TimeField()
    local = models.CharField(max_length=200, blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    quantidade_participantes = models.PositiveIntegerField(null=True, blank=True)
    sem_limites = models.BooleanField(default=False)
    organizador = models.CharField(max_length=200, null=True, blank=True)
    criador = dj_models.ForeignKey(
        'usuarios.Usuario',
        on_delete=dj_models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos_criados'
    )

    # -------------------------------
    # Upload da thumbnail do evento
    # -------------------------------

    def evento_thumb_upload_to(instance, filename):
        """
        Define o caminho de upload da imagem principal (thumb) do evento.
        Sempre substitui a anterior com nome fixo 'thumb.ext'.
        """
        date_str = instance.data_inicio.strftime('%Y_%m_%d') if instance.data_inicio else 'sem_data'
        slug = slugify(instance.titulo)
        ext = os.path.splitext(filename)[1]
        return f'eventos/{date_str}_{slug}/thumb{ext}'


    thumb = models.ImageField(upload_to=evento_thumb_upload_to, blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    horas = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Campos auxiliares
    gallery_slug = models.CharField(max_length=255, blank=True, null=True)
    finalizado = models.BooleanField(default=False)

    def __str__(self):
        """
        Retorna uma representação legível do evento, incluindo título e tipo.
        """
        tipo_label = getattr(self.tipo, 'tipo', str(self.tipo)) if self.tipo else ''
        return f"{self.titulo} - {tipo_label}"

    def get_gallery_name(self):
        """
        Gera o nome da pasta da galeria de imagens do evento.
        """
        slug = slugify(self.titulo)
        date_s = self.data_inicio.strftime('%Y_%m_%d') if self.data_inicio else 'sem_data'
        return f"{date_s}_{slug}"

    def clean(self):
        """
        Validação personalizada do modelo Evento.
        Garante que pelo menos local ou link estejam preenchidos e que as datas estejam corretas.
        """
        if not self.local and not self.link:
            raise ValidationError("Informe pelo menos um: local ou link.")
        if self.data_fim and self.data_inicio and self.data_fim < self.data_inicio:
            raise ValidationError("A data de término não pode ser anterior à data de início.")

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para:
        - Gerar slug da galeria automaticamente
        - Criar pastas do evento e galeria
        - Remover thumb antiga se necessário
        - Redimensionar a imagem da thumb após salvar
        """
        # Gera o slug da galeria automaticamente, se não existir
        if not self.gallery_slug:
            self.gallery_slug = slugify(f"{self.titulo}-{self.data_inicio}")

        # Cria pastas do evento e galeria
        date_str = self.data_inicio.strftime('%Y_%m_%d') if self.data_inicio else 'sem_data'
        event_dir_name = f"{date_str}_{slugify(self.titulo)}"
        event_base = os.path.join(settings.MEDIA_ROOT, 'eventos', event_dir_name)
        os.makedirs(event_base, exist_ok=True)
        galeria_dir = os.path.join(event_base, 'galeria')
        os.makedirs(galeria_dir, exist_ok=True)

        # Remove thumb antiga se for substituir
        if self.pk and self.thumb:
            old_instance = Evento.objects.filter(pk=self.pk).first()
            if old_instance and old_instance.thumb and old_instance.thumb.name != self.thumb.name:
                old_path = os.path.join(settings.MEDIA_ROOT, old_instance.thumb.name)
                if os.path.exists(old_path):
                    os.remove(old_path)

        # SALVA PRIMEIRO para ter o arquivo físico
        super().save(*args, **kwargs)

        # DEPOIS redimensiona a thumb se ela existir
        if self.thumb:
            try:
                thumb_path = self.thumb.path
                if os.path.exists(thumb_path):
                    resize_image(thumb_path, max_size=(400, 400), quality=70)
            except Exception as e:
                print(f"Erro ao redimensionar thumb do evento: {e}")


# ============================================================
# MODELO: InscricaoEvento
# ============================================================

class InscricaoEvento(models.Model):
    """
    Modelo que representa a inscrição de um usuário em um evento.

    Campos:
        evento (ForeignKey): Evento ao qual o usuário está inscrito.
        inscrito (ForeignKey): Usuário inscrito.
        is_validated (BooleanField): Indica se a inscrição foi validada.
        data_inscricao (DateTimeField): Data/hora da inscrição.
    """
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)
    inscrito = dj_models.ForeignKey('usuarios.Usuario', on_delete=dj_models.CASCADE)
    is_validated = models.BooleanField(default=False)
    data_inscricao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        Retorna uma representação legível da inscrição, incluindo usuário e evento.
        """
        return f"{self.inscrito.nome_usuario} inscrito em {self.evento.titulo}"

    def is_complete(self):
        """
        Indica se a inscrição está validada e o evento finalizado.
        """
        return self.is_validated and self.evento.finalizado