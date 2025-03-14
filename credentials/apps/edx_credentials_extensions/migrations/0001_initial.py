from django.db import migrations


def add_siteconfiguration_data(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    SiteConfiguration = apps.get_model("core", "SiteConfiguration")

    site, __ = Site.objects.get_or_create(id=1, defaults={"domain": "example.com", "name": "example.com"})
    defaults = {
        "platform_name": "edX",
        "tos_url": "https://www.edx.org/edx-terms-service",
        "privacy_policy_url": "https://www.edx.org/edx-privacy-policy",
        "homepage_url": "https://www.edx.org",
        "company_name": "edX Inc.",
        "certificate_help_url": "https://docs.openedx.org/en/latest/educators/concepts/open_edx_platform/about_certificates.html",
        "theme_name": "edx.org",
    }
    SiteConfiguration.objects.update_or_create(site=site, defaults=defaults)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_auto_20170119_1205"),
    ]

    operations = [migrations.RunPython(add_siteconfiguration_data, migrations.RunPython.noop)]
