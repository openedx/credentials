# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credentials', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='siteconfiguration',
            name='site',
        ),
        migrations.AlterModelOptions(
            name='coursecertificate',
            options={'verbose_name': 'Course certificate configuration'},
        ),
        migrations.AlterModelOptions(
            name='programcertificate',
            options={'verbose_name': 'Program certificate configuration'},
        ),
        migrations.DeleteModel(
            name='SiteConfiguration',
        ),
    ]
