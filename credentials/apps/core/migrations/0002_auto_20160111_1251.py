# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from credentials.apps.core.constants import Role


def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')

    for name in (Role.LEARNERS, Role.ADMINS):
        Group.objects.get_or_create(name=name)


def destroy_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=(Role.LEARNERS, Role.ADMINS)).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups, reverse_code=destroy_groups),
    ]
