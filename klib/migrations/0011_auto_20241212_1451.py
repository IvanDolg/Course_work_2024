# Generated by Django 2.2.12 on 2024-12-12 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('klib', '0010_auto_20241212_1451'),
    ]

    operations = [
        migrations.AlterField(
            model_name='baseorder',
            name='filing',
            field=models.IntegerField(blank=True, choices=[(2005, 2005), (2006, 2006), (2007, 2007), (2008, 2008), (2009, 2009), (2010, 2010), (2011, 2011), (2012, 2012), (2013, 2013), (2014, 2014), (2015, 2015), (2016, 2016), (2017, 2017), (2018, 2018), (2019, 2019), (2020, 2020), (2021, 2021), (2022, 2022), (2023, 2023), (2024, 2024)], max_length=255, null=True, verbose_name='Filing'),
        ),
    ]
