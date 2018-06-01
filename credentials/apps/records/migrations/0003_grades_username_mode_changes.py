# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-06-04 17:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0002_auto_20180611_1809'),
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usergrade',
            name='username',
            field=models.CharField(default='', max_length=150),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='usergrade',
            unique_together=set([('username', 'course_run')]),
        ),
        migrations.RemoveField(
            model_name='usergrade',
            name='user',
        ),
        migrations.RemoveField(
            model_name='usergrade',
            name='mode',
        ),
        migrations.AddField(
            model_name='usergrade',
            name='verified',
            field=models.BooleanField(default=True, verbose_name='Verified Learner ID'),
        ),
    ]
