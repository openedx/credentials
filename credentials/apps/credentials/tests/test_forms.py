
from unittest import mock

import factory
from django.test import TestCase

from credentials.apps.core.models import SiteConfiguration
from credentials.apps.core.tests.factories import SiteConfigurationFactory
from credentials.apps.credentials.forms import ProgramCertificateAdminForm
from credentials.apps.credentials.tests.factories import ProgramCertificateFactory


class ProgramCertificateAdminFormTests(TestCase):
    BAD_MOCK_API_PROGRAM = {
        'authoring_organizations': [
            {
                'certificate_logo_image_url': None,
            }
        ],
    }

    GOOD_MOCK_API_PROGRAM = {
        'authoring_organizations': [
            {
                'certificate_logo_image_url': 'https://example.com',
            }
        ],
    }

    def test_program_uuid(self):
        """ Verify a ValidationError is raised if the program's authoring organizations have
        no certificate images. """
        sc = SiteConfigurationFactory()
        data = factory.build(dict, FACTORY_CLASS=ProgramCertificateFactory)
        data['site'] = sc.site.id

        form = ProgramCertificateAdminForm(data)
        with mock.patch.object(SiteConfiguration, 'get_program', return_value=self.BAD_MOCK_API_PROGRAM) as mock_method:
            self.assertFalse(form.is_valid())
            mock_method.assert_called_with(data['program_uuid'], ignore_cache=True)
            self.assertEqual(
                form.errors['program_uuid'][0],
                'All authoring organizations of the program MUST have a certificate image defined!'
            )

        form = ProgramCertificateAdminForm(data)
        with mock.patch.object(SiteConfiguration, 'get_program',
                               return_value=self.GOOD_MOCK_API_PROGRAM) as mock_method:
            self.assertFalse(form.is_valid())
            mock_method.assert_called_with(data['program_uuid'], ignore_cache=True)
            self.assertNotIn('program_uuid', form.errors)
