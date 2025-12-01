import os, sys
sys.path.insert(0, '/home/mpqfreitas/code/SiteEventoEnsina/instituicao_ensino')
os.environ.setdefault('DJANGO_SETTINGS_MODULE','instituicao_ensino.settings')
import django
django.setup()
from usuarios.models import Usuario
from eventos.models import TipoEvento, Evento
from usuarios.models import AuditLog
import datetime

USERNAME = 'org_teste'

def main():
    usuario = Usuario.objects.filter(nome_usuario=USERNAME).first()
    if not usuario:
        print(f'Usuario with nome_usuario="{USERNAME}" not found')
        return
    print(f'Found usuario: id={usuario.id} nome_usuario={usuario.nome_usuario} nome={usuario.nome}')

    tipo, _ = TipoEvento.objects.get_or_create(tipo='TesteAuditTipo')
    ev = Evento.objects.create(
        titulo=f'Evento de Auditoria {datetime.datetime.now().isoformat()}',
        tipo=tipo,
        modalidade='online',
        data_inicio=datetime.date.today(),
        data_fim=datetime.date.today(),
        horario='12:00',
        criador=usuario,
    )
    print(f'Created Evento id={ev.id} titulo="{ev.titulo}"')

    print('\nLast 10 AuditLog entries:')
    for a in AuditLog.objects.all().order_by('-timestamp')[:10]:
        print(a.timestamp, getattr(a.usuario, 'nome_usuario', None), getattr(a.django_user, 'username', None), a.action, a.object_type, a.object_id, a.description)

if __name__ == '__main__':
    main()
