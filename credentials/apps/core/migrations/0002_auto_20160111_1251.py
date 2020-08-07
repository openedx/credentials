from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.management import create_permissions
from django.db import migrations

from credentials.apps.core.constants import Role


def create_groups(apps, schema_editor):
    """ Create groups and assign the permissions."""
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, verbosity=0, apps=apps)
        app_config.models_module = None

    group, __ = Group.objects.get_or_create(name=Role.ADMINS)
    for codename in ['add_usercredential', 'change_usercredential']:
        permission = Permission.objects.get(codename=codename)
        group.permissions.add(permission)


def destroy_groups(apps, schema_editor):
    """ First remove the permissions and then delete the groups."""
    Group = apps.get_model('auth', 'Group')
    Group.objects.get(name=Role.ADMINS).delete()

def add_service_user(apps, schema_editor):
    """ Add service user."""
    User = apps.get_model('core', 'User')
    Group = apps.get_model('auth', 'Group')
    user = User.objects.create(username=settings.CREDENTIALS_SERVICE_USER, is_staff=True)
    user.password = make_password(None)
    admin_group = Group.objects.get(name=Role.ADMINS)
    user.groups.add(admin_group)
    user.save()


def remove_service_user(apps, schema_editor):
    """ Remove service user."""
    User = apps.get_model('core', 'User')
    try:
        User.objects.get(username=settings.CREDENTIALS_SERVICE_USER).delete()
    except User.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('credentials', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(code=create_groups, reverse_code=destroy_groups),
        migrations.RunPython(code=add_service_user, reverse_code=remove_service_user),
    ]
