"""Remove field `ddd` from Usuario model.

This migration drops the `ddd` column. Existing phone values will remain
in `telefone` which stores the full international phone. Run with a DB
backup if you have important data.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0020_remove_ddd_model'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usuario',
            name='ddd',
        ),
    ]
