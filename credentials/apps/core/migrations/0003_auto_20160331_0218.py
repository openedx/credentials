from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import migrations

from credentials.apps.core.constants import Role


def create_view_permission(apps, schema_editor):
    """
    Add an explicit view permission for UserCredential, and associate it with
    the ADMIN role.
    """
    content_type = ContentType.objects.get(app_label="credentials", model="usercredential")

    # Django2.1 is creating view permission by default now. Adding check otherwise unique constraints triggers.
    if not Permission.objects.filter(content_type=content_type, codename='view_usercredential').exists():
        permission, created = Permission.objects.get_or_create(
            content_type=content_type,
            codename='view_usercredential',
            name='Can view any user credential',
        )
        if created:
            Group.objects.get(name=Role.ADMINS).permissions.add(permission)


def destroy_view_permission(apps, schema_editor):
    """
    Remove the view permission, if it exists.  Note that the permission will
    automatically be removed from any roles to which it had been linked.
    """
    try:
        content_type = ContentType.objects.get(app_label='credentials', model='usercredential')
        permission = Permission.objects.get(content_type=content_type, codename='view_usercredential')
        permission.delete()
    except ObjectDoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20160111_1251'),
    ]

    operations = [
        migrations.RunPython(code=create_view_permission, reverse_code=destroy_view_permission),
    ]
