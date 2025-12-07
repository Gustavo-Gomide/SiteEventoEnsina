from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.conf import settings
from notifications.models import EmailJob
import mimetypes


class Command(BaseCommand):
    help = 'Processa fila de e-mails pendentes (EmailJob).'

    def add_arguments(self, parser):
        parser.add_argument('--max', type=int, default=50, help='Máximo de e-mails por execução')

    def handle(self, *args, **options):
        max_jobs = options['max']
        now = timezone.now()
        jobs = EmailJob.objects.select_for_update(skip_locked=True).filter(status='pending', scheduled_at__lte=now)[:max_jobs]
        processed = 0
        for job in jobs:
            processed += 1
            try:
                job.status = 'sending'
                job.save(update_fields=['status', 'updated_at'])

                msg = EmailMultiAlternatives(
                    subject=job.subject,
                    body=job.text_body or '',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                    to=[job.to_email],
                )
                if job.html_body:
                    msg.attach_alternative(job.html_body, 'text/html')

                # Attach files
                for att in (job.attachments or []):
                    try:
                        path = att.get('path')
                        name = att.get('name') or (path.split('/')[-1] if path else 'anexo')
                        ctype = att.get('mimetype') or mimetypes.guess_type(path)[0] or 'application/octet-stream'
                        with open(path, 'rb') as f:
                            msg.attach(name, f.read(), ctype)
                    except Exception:
                        # continue without blocking other attachments
                        continue

                msg.send(fail_silently=False)
                job.status = 'sent'
                job.sent_at = timezone.now()
                job.last_error = ''
                job.save(update_fields=['status', 'sent_at', 'last_error', 'updated_at'])
                self.stdout.write(self.style.SUCCESS(f"Enviado: {job.to_email} - {job.subject}"))
            except Exception as e:
                job.retries += 1
                job.status = 'pending' if job.retries < 5 else 'failed'
                # Exponential backoff: 2^retries minutes
                delay_minutes = 2 ** min(job.retries, 5)
                job.scheduled_at = timezone.now() + timezone.timedelta(minutes=delay_minutes)
                job.last_error = str(e)[:1000]
                job.save(update_fields=['retries', 'status', 'scheduled_at', 'last_error', 'updated_at'])
                self.stderr.write(self.style.WARNING(f"Falha ao enviar para {job.to_email}: {e}"))

        self.stdout.write(self.style.NOTICE(f"Total processado: {processed}"))
