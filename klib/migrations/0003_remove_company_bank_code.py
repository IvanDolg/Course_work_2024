# Generated by Django 2.2.12 on 2024-12-03 13:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('klib', '0002_auto_20241127_1926'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='company',
            name='bank_code',
        ),
    ]
