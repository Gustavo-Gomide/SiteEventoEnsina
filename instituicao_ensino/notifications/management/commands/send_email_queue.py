
"""
Comando Django customizado para processar a fila de e-mails pendentes (EmailJob).
Envia e-mails agendados, trata anexos, atualiza status e faz retentativas automáticas com backoff exponencial.
"""

from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.conf import settings
from notifications.models import EmailJob
import mimetypes



class Command(BaseCommand):
    """
    Comando para processar e enviar e-mails pendentes da fila (EmailJob).
    Pode ser executado manualmente ou via agendamento (cron/task scheduler).
    """
    help = 'Processa fila de e-mails pendentes (EmailJob).'

    def add_arguments(self, parser):
        """
        Adiciona argumento opcional '--max' para limitar o número de e-mails processados por execução.
        """
        parser.add_argument('--max', type=int, default=50, help='Máximo de e-mails por execução')

    def handle(self, *args, **options):
        """
        Executa o processamento da fila de e-mails:
        - Busca até 'max' e-mails pendentes e agendados para envio.
        - Atualiza status para 'sending', envia o e-mail (com anexos, se houver),
          e marca como 'sent' ou reprograma em caso de erro.
        - Faz retentativas automáticas com backoff exponencial até 5 tentativas.
        """
        max_jobs = options['max']
        now = timezone.now()
        # Busca e-mails pendentes, bloqueando para evitar concorrência
        jobs = EmailJob.objects.select_for_update(skip_locked=True).filter(status='pending', scheduled_at__lte=now)[:max_jobs]
        processed = 0
        for job in jobs:
            processed += 1
            try:
                # Marca como enviando
                job.status = 'sending'
                job.save(update_fields=['status', 'updated_at'])

                # Monta a mensagem de e-mail
                msg = EmailMultiAlternatives(
                    subject=job.subject,
                    body=job.text_body or '',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                    to=[job.to_email],
                )
                if job.html_body:
                    msg.attach_alternative(job.html_body, 'text/html')

                # Anexa arquivos, se houver
                for att in (job.attachments or []):
                    try:
                        path = att.get('path')
                        name = att.get('name') or (path.split('/')[-1] if path else 'anexo')
                        ctype = att.get('mimetype') or mimetypes.guess_type(path)[0] or 'application/octet-stream'
                        with open(path, 'rb') as f:
                            msg.attach(name, f.read(), ctype)
                    except Exception:
                        # Ignora erro de anexo individual, segue com os demais
                        continue

                # Envia o e-mail
                msg.send(fail_silently=False)
                job.status = 'sent'
                job.sent_at = timezone.now()
                job.last_error = ''
                job.save(update_fields=['status', 'sent_at', 'last_error', 'updated_at'])
                self.stdout.write(self.style.SUCCESS(f"Enviado: {job.to_email} - {job.subject}"))
            except Exception as e:
                # Em caso de erro, incrementa retentativas e reprograma
                job.retries += 1
                job.status = 'pending' if job.retries < 5 else 'failed'
                # Backoff exponencial: 2^retries minutos
                delay_minutes = 2 ** min(job.retries, 5)
                job.scheduled_at = timezone.now() + timezone.timedelta(minutes=delay_minutes)
                job.last_error = str(e)[:1000]
                job.save(update_fields=['retries', 'status', 'scheduled_at', 'last_error', 'updated_at'])
                self.stderr.write(self.style.WARNING(f"Falha ao enviar para {job.to_email}: {e}"))

        self.stdout.write(self.style.NOTICE(f"Total processado: {processed}"))
