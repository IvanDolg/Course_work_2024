# Generated by Django 2.2.12 on 2024-12-13 09:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('klib', '0012_auto_20241212_1451'),
    ]

    operations = [
        migrations.AddField(
            model_name='basearrival',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='klib.Company', verbose_name='Company'),
        ),
    ]
