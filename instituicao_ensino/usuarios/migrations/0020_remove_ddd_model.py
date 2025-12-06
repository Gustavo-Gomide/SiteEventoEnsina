from django.db import migrations, models


def forwards(apps, schema_editor):
    DDD = apps.get_model('usuarios', 'DDD')
    Usuario = apps.get_model('usuarios', 'Usuario')
    for u in Usuario.objects.all():
        try:
            # prior to migration, Usuario has a FK field `ddd_id`
            ddd_id = getattr(u, 'ddd_id', None)
            if ddd_id:
                d = DDD.objects.filter(pk=ddd_id).first()
                if d:
                    u.ddd_temp = d.codigo
                    u.save(update_fields=['ddd_temp'])
        except Exception:
            # não interrompe a migração por registro problemático
            pass


def backwards(apps, schema_editor):
    # recria DDDs a partir dos códigos presentes em ddd_temp e refaz o FK
    DDD = apps.get_model('usuarios', 'DDD')
    Usuario = apps.get_model('usuarios', 'Usuario')
    codes = set()
    for u in Usuario.objects.all():
        code = getattr(u, 'ddd_temp', None)
        if code:
            codes.add(code)
    created = {}
    for code in codes:
        try:
            d = DDD.objects.create(codigo=code, pais='Brasil')
            created[code] = d
        except Exception:
            pass
    for u in Usuario.objects.all():
        try:
            code = getattr(u, 'ddd_temp', None)
            if code and code in created:
                u.ddd = created[code]
                u.save(update_fields=['ddd'])
        except Exception:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0019_alter_instituicao_telefone_alter_usuario_telefone'),
    ]

    operations = [
        # 1) adiciona campo temporário para guardar o código do DDD
        migrations.AddField(
            model_name='usuario',
            name='ddd_temp',
            field=models.CharField(max_length=3, null=True, blank=True),
        ),
        # 2) copia os dados do FK para o campo temporário
        migrations.RunPython(forwards, backwards),
        # 3) remove o campo FK 'ddd'
        migrations.RemoveField(
            model_name='usuario',
            name='ddd',
        ),
        # 4) deleta o modelo DDD
        migrations.DeleteModel(
            name='DDD',
        ),
        # 5) renomeia ddd_temp para ddd
        migrations.RenameField(
            model_name='usuario',
            old_name='ddd_temp',
            new_name='ddd',
        ),
    ]
