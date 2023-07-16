
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("forms", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Question",
            fields=[
                (
                    "question_id",
                    models.AutoField(
                        db_column="question_id", primary_key=True, serialize=False
                    ),
                ),
                ("content", models.TextField()),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(blank=True, null=True)),
                (
                    "form_id",
                    models.ForeignKey(
                        db_column="form_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="questions",
                        to="forms.form",
                    ),
                ),
            ],
            options={
                "db_table": "question",
            },
        ),
        migrations.CreateModel(
            name="Answer",
            fields=[
                (
                    "answer_id",
                    models.AutoField(
                        db_column="answer_id", primary_key=True, serialize=False
                    ),
                ),
                ("content", models.TextField()),
                ("recode_file", models.CharField(max_length=200)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(blank=True, null=True)),
                (
                    "question_id",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="speak_to_chat.question",
                    ),
                ),

            ],
            options={
                "db_table": "answer",
            },
        ),
    ]
