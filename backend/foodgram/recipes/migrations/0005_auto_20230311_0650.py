# Generated by Django 2.2.19 on 2023-03-11 06:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_auto_20230311_0648'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recipes',
            old_name='is_favourited',
            new_name='is_favorited',
        ),
    ]
