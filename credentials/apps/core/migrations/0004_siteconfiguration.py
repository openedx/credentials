# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        ('core', '0003_auto_20160114_1001'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lms_url_root', models.URLField(help_text="Root URL of this site's LMS (e.g. https://courses.stage.edx.org)", verbose_name='LMS base url for custom site')),
                ('logo_url', models.URLField(help_text="Absolute URL of this site's logo (e.g. https://www.edx.org/sites/default/files/theme/edx-logo-header.png)", verbose_name="URL of site's logo")),
                ('theme_scss_path', models.CharField(help_text='Path to scss files of the custom site theme', max_length=255, verbose_name='Path to custom site theme')),
                ('site', models.OneToOneField(to='sites.Site')),
            ],
        ),
    ]
