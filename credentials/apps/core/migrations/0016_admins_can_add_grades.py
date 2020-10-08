from django.db import migrations

from credentials.apps.core.constants import Role


def add_perm(apps, schema_editor):
    """ Assign the permission."""
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    group, _ = Group.objects.get_or_create(name=Role.ADMINS)
    for permission in Permission.objects.filter(codename__in=['add_usergrade', 'change_usergrade']):
        group.permissions.add(permission)


def remove_perm(apps, schema_editor):
    """ Remove the permission."""
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    group, _ = Group.objects.get_or_create(name=Role.ADMINS)
    for permission in Permission.objects.filter(codename__in=['add_usergrade', 'change_usergrade']):
        group.permissions.remove(permission)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_siteconfiguration_records_help_url'),
        ('records', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(code=add_perm, reverse_code=remove_perm),
    ]
