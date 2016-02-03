""" Core models. """

from django.contrib.auth.models import AbstractUser
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import ugettext_lazy as _


class SiteConfiguration(models.Model):
    """
    Site configuration model for custom credentials sites.
    """
    site = models.OneToOneField(Site, null=False, blank=False)
    lms_url_root = models.URLField(
        verbose_name=_('LMS base url for custom site'),
        help_text=_("Root URL of this site's LMS (e.g. https://courses.stage.edx.org)"),
        null=False,
        blank=False
    )
    theme_scss_path = models.CharField(
        verbose_name=_('Path to custom site theme'),
        help_text=_("Path to site theme's main SCSS file"),
        max_length=255,
        null=False,
        blank=False
    )

    def __unicode__(self):
        return unicode(self.site.name)


class User(AbstractUser):
    """ Custom user model for use with OpenID Connect. """
    full_name = models.CharField(_('Full Name'), max_length=255, blank=True, null=True)

    @property
    def access_token(self):
        """ Returns an OAuth2 access token for this user, if one exists; otherwise None.

        Assumes user has authenticated at least once with edX Open ID Connect.
        """
        try:
            return self.social_auth.first().extra_data[u'access_token']  # pylint: disable=no-member
        except Exception:  # pylint: disable=broad-except
            return None

    class Meta(object):  # pylint:disable=missing-docstring
        get_latest_by = 'date_joined'

    def __unicode__(self):
        return unicode(self.full_name)

    def get_full_name(self):
        return self.full_name or super(User, self).get_full_name()
