import os, sys
sys.path.insert(0, '/home/mpqfreitas/code/SiteEventoEnsina/instituicao_ensino')
os.environ.setdefault('DJANGO_SETTINGS_MODULE','instituicao_ensino.settings')
import django
django.setup()
from django.test import Client
from django.urls import reverse

USERNAME = 'org_teste'
PASSWORD = 'testpass'

c = Client()
logged = c.login(username=USERNAME, password=PASSWORD)
print('login:', logged)
try:
    url = reverse('auditoria_eventos')
except Exception:
    url = '/eventos/auditoria/'
resp = c.get(url)
print('status_code:', getattr(resp, 'status_code', None))
if hasattr(resp, 'url'):
    print('redirect to:', resp.url)
if hasattr(resp, 'content'):
    print('content_snippet:')
    content = resp.content.decode('utf-8', errors='replace')
    print(content[:1000])
