# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-02-15 17:34
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('credentials', '0007_auto_20170118_2111'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='programcertificate',
            name='program_id',
        ),
    ]
