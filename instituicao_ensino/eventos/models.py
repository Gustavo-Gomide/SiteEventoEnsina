import os
from django.db import models
from django.conf import settings
from django.db import models as dj_models
from django.core.exceptions import ValidationError
from django.utils.text import slugify


# ============================================================
# MODELO: TipoEvento
# ============================================================
class TipoEvento(models.Model):
    """
    Armazena os tipos de eventos disponíveis (Ex: Palestra, Oficina, Curso).
    """
    tipo = models.CharField(max_length=50, unique=True)  # campo único para evitar duplicados

    def __str__(self):
        # Retorna o nome do tipo de evento (ex: "Palestra")
        return self.tipo


# ============================================================
# MODELO: Evento
# ============================================================
class Evento(models.Model):
    """
    Representa um evento no sistema, com dados como título, tipo, datas,
    local, imagens e pastas de mídia gerenciadas automaticamente.
    """

    # -------------------------------
    # Escolhas para modalidade
    # -------------------------------
    MODALIDADES = [
        ('online', 'Online'),
        ('presencial', 'Presencial'),
        ('hibrido', 'Híbrido'),
    ]

    # -------------------------------
    # Campos principais
    # -------------------------------
    titulo = models.CharField(max_length=200)
    tipo = models.ForeignKey(TipoEvento, on_delete=models.CASCADE)
    modalidade = models.CharField(max_length=10, choices=MODALIDADES)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    horario = models.TimeField()

    # -------------------------------
    # Local ou link (um dos dois é obrigatório)
    # -------------------------------
    local = models.CharField(max_length=200, blank=True, null=True)
    link = models.URLField(blank=True, null=True)

    # -------------------------------
    # Participantes e organização
    # -------------------------------
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
        Define o caminho da imagem principal (thumb) do evento.
        Exemplo:
            media/eventos/2025_10_11_meu_evento/thumb.jpg
        """
        date_str = instance.data_inicio.strftime('%Y_%m_%d') if instance.data_inicio else 'sem_data'
        nome = slugify(instance.titulo)
        base, ext = os.path.splitext(filename)
        return f'eventos/{date_str}_{nome}/thumb{ext}'

    thumb = models.ImageField(upload_to=evento_thumb_upload_to, blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    horas = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # -------------------------------
    # Campos auxiliares
    # -------------------------------
    gallery_slug = models.CharField(max_length=255, blank=True, null=True)
    finalizado = models.BooleanField(default=False)

    # -------------------------------
    # Representação do objeto
    # -------------------------------
    def __str__(self):
        tipo_label = getattr(self.tipo, 'tipo', str(self.tipo)) if self.tipo else ''
        return f"{self.titulo} - {tipo_label}"

    # -------------------------------
    # Nome para a pasta da galeria
    # -------------------------------
    def get_gallery_name(self):
        """
        Retorna um nome único e legível para a galeria do evento.
        Exemplo: "meu_evento-2025-10-11"
        """
        slug = slugify(self.titulo)
        date_s = self.data_inicio.strftime('%Y_%m_%d') if self.data_inicio else 'sem_data'
        return f"{date_s}_{slug}"

    # -------------------------------
    # Validação personalizada
    # -------------------------------
    def clean(self):
        """
        Regras de validação antes de salvar:
        - Deve haver pelo menos local OU link.
        - A data final não pode ser anterior à data inicial.
        """
        if not self.local and not self.link:
            raise ValidationError("Informe pelo menos um: local ou link.")
        if self.data_fim and self.data_inicio and self.data_fim < self.data_inicio:
            raise ValidationError("A data de término não pode ser anterior à data de início.")

    # -------------------------------
    # Sobrescrita do método save()
    # -------------------------------
    def save(self, *args, **kwargs):
        """
        Cria automaticamente a estrutura de pastas do evento:
        media/eventos/<data>_<slug>/
            ├── thumb.jpg
            └── galeria/
        """
        # Gera o slug da galeria automaticamente, se não existir
        if not self.gallery_slug:
            self.gallery_slug = slugify(f"{self.titulo}-{self.data_inicio}")

        # Define o nome da pasta do evento com data + título slugificado
        date_str = self.data_inicio.strftime('%Y_%m_%d') if self.data_inicio else 'sem_data'
        event_dir_name = f"{date_str}_{slugify(self.titulo)}"
        event_base = os.path.join(settings.MEDIA_ROOT, 'eventos', event_dir_name)

        # Cria a pasta principal e a subpasta da galeria
        os.makedirs(event_base, exist_ok=True)
        galeria_dir = os.path.join(event_base, 'galeria')
        os.makedirs(galeria_dir, exist_ok=True)

        # Chama o método original do Django para salvar o objeto
        super().save(*args, **kwargs)


# ============================================================
# MODELO: InscricaoEvento
# ============================================================
class InscricaoEvento(models.Model):
    """
    Relaciona o usuário (inscrito) com um evento,
    registrando se foi validado e quando se inscreveu.
    """
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)
    inscrito = dj_models.ForeignKey('usuarios.Usuario', on_delete=dj_models.CASCADE)
    is_validated = models.BooleanField(default=False)
    data_inscricao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Exibe no admin ou shell: "<inscrito> inscrito em <evento>"
        return f"{self.inscrito.nome_usuario} inscrito em {self.evento.titulo}"

    def is_complete(self):
        """
        Retorna True se a inscrição foi validada e o evento finalizado.
        Pode ser usado para liberar certificados automaticamente.
        """
        return self.is_validated and self.evento.finalizado
