# Generated by Django 2.2.12 on 2024-12-12 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('klib', '0008_baseorder_year'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseorder',
            name='filing',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Filing'),
        ),
    ]
