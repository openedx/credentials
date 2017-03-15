from django.contrib.sites.models import Site
from django.db.models.signals import pre_delete, pre_save

from credentials.apps.core.models import SiteConfiguration


def clear_site_cache(sender, **kwargs):  # pylint: disable=unused-argument
    Site.objects.clear_cache()


# Clear the Site cache to force a refresh of related SiteConfiguration objects
pre_delete.connect(clear_site_cache, sender=SiteConfiguration, dispatch_uid='pre_delete_siteconfiguration_clear_cache')
pre_save.connect(clear_site_cache, sender=SiteConfiguration, dispatch_uid='pre_save_siteconfiguration_clear_cache')
