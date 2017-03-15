import ddt
from django.test import TestCase

from credentials.apps.core.forms import SiteConfigurationAdminForm


@ddt.ddt
class SiteConfigurationAdminFormTests(TestCase):
    @ddt.data('', None)
    def test_clean_with_invalid_facebook_config(self, app_id):
        """ Verify a Facebook app ID is required if Facebook sharing is enabled. """
        data = {
            'facebook_app_id': app_id,
            'enable_facebook_sharing': True,
        }
        form = SiteConfigurationAdminForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('facebook_app_id', 'required_for_sharing'))
