
"""
Modelos para gerenciamento de fila de envio de emails em background.
"""

from django.db import models
from django.utils import timezone



class EmailJob(models.Model):
    """
    Modelo que representa um job de envio de email na fila de background.

    Campos:
        to_email (EmailField): Destinatário do email.
        subject (CharField): Assunto do email.
        text_body (TextField): Corpo do email em texto simples.
        html_body (TextField): Corpo do email em HTML.
        attachments (JSONField): Lista de anexos (dicionários com path, nome, mimetype).
        status (CharField): Status do envio ('pending', 'sending', 'sent', 'failed').
        retries (PositiveSmallIntegerField): Número de tentativas de envio.
        scheduled_at (DateTimeField): Data/hora agendada para envio.
        sent_at (DateTimeField): Data/hora em que foi enviado.
        last_error (TextField): Último erro ocorrido no envio.
        created_at (DateTimeField): Data/hora de criação do job.
        updated_at (DateTimeField): Data/hora da última atualização.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )

    to_email = models.EmailField()
    subject = models.CharField(max_length=255)
    text_body = models.TextField(blank=True, null=True)
    html_body = models.TextField(blank=True, null=True)
    attachments = models.JSONField(blank=True, null=True)  # list of {path, name, mimetype}
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending', db_index=True)
    retries = models.PositiveSmallIntegerField(default=0)
    scheduled_at = models.DateTimeField(default=timezone.now, db_index=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    last_error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        """
        Retorna uma representação legível do job de email para exibição/admin.
        """
        return f"EmailJob(to={self.to_email}, subject={self.subject}, status={self.status})"
