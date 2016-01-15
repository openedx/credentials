# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.models import Permission, Group

from django.db import migrations
from django.conf import settings
from credentials.apps.core.constants import Role

from credentials.apps.core.models import User


def add_service_user(apps, schema_editor):
    """Add service user."""
    user, __ = User.objects.get_or_create(username=settings.CREDENTIALS_SERVICE_USER, is_staff=True)
    user.set_unusable_password()
    admin_group = Group.objects.get(name=Role.ADMINS)
    user.groups.add(admin_group)
    user.save()


def remove_service_user(apps, schema_editor):
    """Remove service user."""
    try:
        User.objects.get(username=settings.CREDENTIALS_SERVICE_USER).delete()
    except User.DoesNotExist:
        pass


def add_permissions_for_admins_group(apps, schema_editor):
    """ Add permissions of add and update credentials for user_group admins. """
    group, __ = Group.objects.get_or_create(name=Role.ADMINS)
    permissions = Permission.objects.filter(codename__in=["add_usercredential", "change_usercredential"])
    group.permissions = permissions
    group.save()


def clear_permissions_for_admins_group(apps, schema_editor):
    """ Clears permissions of add and update credentials for user_group admins. """
    try:
        admins_group = Group.objects.get(name=Role.ADMINS)
    except Group.DoesNotExist:
        return

    admins_group.permissions.clear()
    admins_group.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20160111_1251'),
    ]
    operations = [
        migrations.RunPython(code=add_permissions_for_admins_group, reverse_code=clear_permissions_for_admins_group),
        migrations.RunPython(code=add_service_user, reverse_code=remove_service_user),
    ]

