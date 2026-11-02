from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0010_analize_observacao_usuario'),
    ]

    operations = [
        migrations.AddField(
            model_name='analize',
            name='usuario',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='analises',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
