from django.core.management.base import BaseCommand
from usuarios.models import Usuario
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Migra usuários existentes (usuarios.Usuario) para criar accounts do Django e vincular em Usuario.user'

    def handle(self, *args, **options):
        usuarios = Usuario.objects.filter(user__isnull=True)
        created = 0
        for u in usuarios:
            username = u.nome_usuario
            # se username já existir no User, anexa com sufixo
            if User.objects.filter(username=username).exists():
                username = f"{username}_migrado_{u.id}"
            # tentativa de usar password se estiver presente (hash)
            password = None
            if u.senha:
                # não é possível reusar o hash sem saber o algoritmo com compatibilidade direta,
                # então criamos um usuário com senha aleatória e o administrador pode forçar reset
                password = User.objects.make_random_password()
            user = User.objects.create_user(username=username, password=password or 'change-me')
            u.user = user
            u.save()
            created += 1
            self.stdout.write(self.style.SUCCESS(f'Usuário {u.nome_usuario} migrado para Django User {user.username}'))
        self.stdout.write(self.style.SUCCESS(f'Total migrados: {created}'))
