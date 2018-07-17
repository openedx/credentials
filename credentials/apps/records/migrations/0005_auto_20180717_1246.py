# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-07-17 12:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0003_auto_20180712_2016'),
        ('records', '0004_grades_blank_letter_grade'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='programcertrecord',
            options={'verbose_name': 'A viewable record of a program'},
        ),
        migrations.AddField(
            model_name='programcertrecord',
            name='program',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='catalog.Program'),
        ),
        migrations.AlterField(
            model_name='programcertrecord',
            name='certificate',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='credentials.ProgramCertificate'),
        ),
        migrations.AlterUniqueTogether(
            name='programcertrecord',
            unique_together=set([]),
        ),
    ]
