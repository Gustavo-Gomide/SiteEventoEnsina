import threading
import time
import mimetypes
import socket
from queue import Queue
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from .models import EmailJob


_worker_started = False
_socket_queue: Queue | None = None
_socket_server_thread: threading.Thread | None = None
_socket_host = '127.0.0.1'
_socket_port = int(getattr(settings, 'EMAIL_QUEUE_PORT', 9099))


def _send_job(job: EmailJob):
    """Send a single EmailJob, updating its status accordingly."""
    try:
        # job should already be in 'sending' state
        msg = EmailMultiAlternatives(
            subject=job.subject,
            body=job.text_body or '',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            to=[job.to_email],
        )
        if job.html_body:
            msg.attach_alternative(job.html_body, 'text/html')
        for att in (job.attachments or []):
            try:
                path = att.get('path')
                name = att.get('name') or (path.split('/')[-1] if path else 'anexo')
                ctype = att.get('mimetype') or mimetypes.guess_type(path)[0] or 'application/octet-stream'
                with open(path, 'rb') as f:
                    msg.attach(name, f.read(), ctype)
            except Exception:
                continue
        msg.send(fail_silently=False)
        job.status = 'sent'
        job.sent_at = timezone.now()
        job.last_error = ''
        job.save(update_fields=['status', 'sent_at', 'last_error', 'updated_at'])
    except Exception as e:
        job.retries += 1
        job.status = 'pending' if job.retries < 5 else 'failed'
        delay_minutes = 2 ** min(job.retries, 5)
        job.scheduled_at = timezone.now() + timezone.timedelta(minutes=delay_minutes)
        job.last_error = str(e)[:1000]
        job.save(update_fields=['retries', 'status', 'scheduled_at', 'last_error', 'updated_at'])


def _try_claim_one_pending():
    """Atomically claim one pending job by switching status to 'sending'. Return the claimed job or None."""
    try:
        now = timezone.now()
        job = EmailJob.objects.filter(status='pending', scheduled_at__lte=now).order_by('scheduled_at').first()
        if not job:
            return None
        updated = EmailJob.objects.filter(pk=job.pk, status='pending').update(status='sending', updated_at=timezone.now())
        if updated == 1:
            return EmailJob.objects.get(pk=job.pk)
        return None
    except Exception:
        return None


def push_job(job_id: int):
    """Push a job id into the global socket queue for immediate consumption."""
    global _socket_queue
    if _socket_queue is None:
        return False
    try:
        _socket_queue.put(job_id, block=False)
        return True
    except Exception:
        return False


def start_background_worker(interval_seconds: int = 5, num_cert_threads: int = 2):
    """Start background processing with multiple worker threads polling DB and sending emails."""
    global _worker_started
    if _worker_started:
        return
    # Create global socket queue
    global _socket_queue
    _socket_queue = Queue(maxsize=1000)

    # Start TCP socket server to receive job IDs in real-time
    def socket_server():
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            srv.bind((_socket_host, _socket_port))
            srv.listen(5)
        except Exception:
            return
        while True:
            try:
                conn, _addr = srv.accept()
            except Exception:
                continue
            # read lines of job ids
            try:
                with conn:
                    data = b''
                    while True:
                        chunk = conn.recv(1024)
                        if not chunk:
                            break
                        data += chunk
                    text = data.decode('utf-8', errors='ignore')
                    for part in text.replace('\r','').split('\n'):
                        part = part.strip()
                        if not part:
                            continue
                        try:
                            job_id = int(part)
                            _socket_queue.put(job_id, block=False)
                        except Exception:
                            continue
            except Exception:
                continue

    global _socket_server_thread
    _socket_server_thread = threading.Thread(target=socket_server, name='EmailSocketServer', daemon=True)
    _socket_server_thread.start()

    # Start worker threads (two for certificates as requested)
    def worker_loop(idx: int):
        while True:
            try:
                # Prefer consuming from socket queue if available
                job = None
                try:
                    if _socket_queue is not None:
                        job_id = _socket_queue.get(block=False)
                        try:
                            job = EmailJob.objects.get(pk=job_id)
                            # job should already be 'sending' set by producer; do not re-claim here
                        except EmailJob.DoesNotExist:
                            job = None
                except Exception:
                    job = None

                # Fallback: claim from DB if queue empty
                if job is None:
                    job = _try_claim_one_pending()
                if job is None:
                    time.sleep(interval_seconds)
                    continue
                _send_job(job)
            except Exception:
                time.sleep(interval_seconds)

    for i in range(max(1, num_cert_threads)):
        t = threading.Thread(target=worker_loop, args=(i,), name=f'EmailWorker-{i}', daemon=True)
        t.start()

    _worker_started = True


def send_job_now(job_id: int):
    try:
        job = EmailJob.objects.get(pk=job_id)
    except EmailJob.DoesNotExist:
        return
    if job.status != 'pending':
        return
    # Try to push into socket for immediate processing via queue or TCP
    if push_job(job.id):
        return
    # TCP push as fallback
    try:
        with socket.create_connection((_socket_host, _socket_port), timeout=1.0) as s:
            s.sendall(f"{job.id}\n".encode('utf-8'))
            return
    except Exception:
        pass
    # Fallback: claim and send immediately
    updated = EmailJob.objects.filter(pk=job.pk, status='pending').update(status='sending', updated_at=timezone.now())
    if updated == 1:
        _send_job(EmailJob.objects.get(pk=job.pk))
