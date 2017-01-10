# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def add_siteconfiguration_data(apps, schema_editor):
    SiteConfiguration = apps.get_model('core', 'SiteConfiguration')
    defaults = {
        'platform_name': 'edX',
        'tos_url': 'https://www.edx.org/edx-terms-service',
        'privacy_policy_url': 'https://www.edx.org/edx-privacy-policy',
        'homepage_url': 'https://www.edx.org',
        'company_name': 'edX Inc.',
        'verified_certificate_url': 'https://www.edx.org/verified-certificate',
        'certificate_help_url': 'https://edx.readthedocs.org/projects/edx-guide-for-students/en/latest/SFD_certificates.html#web-certificates',
    }
    SiteConfiguration.objects.update_or_create(site_id=1, defaults=defaults)

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20170119_1205'),
    ]

    operations = [
        migrations.RunPython(add_siteconfiguration_data, migrations.RunPython.noop)
    ]


