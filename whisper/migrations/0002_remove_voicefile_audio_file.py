# Generated by Django 4.2.3 on 2023-07-05 14:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whisper', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='voicefile',
            name='audio_file',
        ),
    ]
