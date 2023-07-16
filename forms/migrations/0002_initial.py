
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('forms', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name="form",
            name="user_id",
            field=models.ForeignKey(
                db_column="user_id",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="forms",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
