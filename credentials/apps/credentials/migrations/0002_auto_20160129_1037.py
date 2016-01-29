# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credentials', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='coursecertificate',
            options={'verbose_name': 'Course certificate configuration'},
        ),
        migrations.AlterModelOptions(
            name='programcertificate',
            options={'verbose_name': 'Program certificate configuration'},
        ),
        migrations.AddField(
            model_name='siteconfiguration',
            name='logo_url',
            field=models.URLField(default='', help_text="Absolute URL of this site's logo (e.g. https://www.edx.org/sites/default/files/theme/edx-logo-header.png)", verbose_name='Logo url for custom site/microsite'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='siteconfiguration',
            name='theme_scss_path',
            field=models.CharField(help_text='Path to scss files of the custom site theme', max_length=255, verbose_name='Path to custom site theme', blank=True),
        ),
    ]
