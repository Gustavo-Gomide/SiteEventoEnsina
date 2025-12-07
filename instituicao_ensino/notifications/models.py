from django.db import models
from django.utils import timezone


class EmailJob(models.Model):
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
        return f"EmailJob(to={self.to_email}, subject={self.subject}, status={self.status})"
