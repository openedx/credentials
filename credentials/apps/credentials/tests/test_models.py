"""Test models for credentials service app."""

import uuid
from unittest import mock

import ddt
from django.core.exceptions import ValidationError
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from opaque_keys.edx.locator import CourseLocator

from credentials.apps.core.models import SiteConfiguration
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials import constants
from credentials.apps.credentials.models import (
    CourseCertificate,
    OrganizationDetails,
    ProgramDetails,
    Signatory,
    UserCredential,
)
from credentials.apps.credentials.tests.factories import (
    ProgramCertificateFactory,
    SignatoryFactory,
    UserCredentialFactory,
)
from credentials.settings.base import MEDIA_ROOT


TEST_DATA_ROOT = MEDIA_ROOT + '/test/data/'


class SignatoryTests(TestCase):
    """Test Signatory model."""

    def get_image(self, name):
        """Get one of the test images from the test data directory."""
        return ImageFile(open(TEST_DATA_ROOT + name + '.png'))

    def create_clean(self, file_obj):
        """
        Shortcut to create a Signatory with a specific file.
        """
        Signatory(name='test_signatory', title='Test Signatory', image=file_obj).full_clean()

    def test_good_image(self):
        """Verify that saving a valid signatory image is no problem."""
        good_image = self.get_image('good')
        Signatory(name='test_signatory', title='Test Signatory', image=good_image).full_clean()

    def test_large_image(self):
        """Upload of large image size should raise validation exception."""
        large_image = self.get_image('large')
        self.assertRaises(ValidationError, self.create_clean, large_image)

    def test_signatory_file_saving(self):
        """
        Verify that asset file is saving with actual name and on correct path.
        """
        image = SimpleUploadedFile('image.jpg', b'file contents!')
        signatory = Signatory.objects.create(name='test name', title='Test Signatory', image=image)

        assert signatory.image.name.startswith('signatories/1/image')
        assert signatory.image.name.endswith('.jpg')

        # Now replace the asset with another file
        signatory.image = SimpleUploadedFile('image_2.jpg', b'file contents')
        signatory.save()

        assert signatory.image.name.startswith('signatories/1/image_2')
        assert signatory.image.name.endswith('.jpg')

    def test_str(self):
        """ Verify the method serializes the Signatory's name and title. """
        signatory = SignatoryFactory()
        self.assertEqual(str(signatory), signatory.name + ', ' + signatory.title)


class CourseCertificateTests(SiteMixin, TestCase):
    """Test Course Certificate model."""

    def setUp(self):
        super().setUp()
        self.course_key = CourseLocator(org='test', course='test', run='test')

    def test_invalid_course_key(self):
        """Test Validation Error occurs for invalid course key."""
        with self.assertRaises(ValidationError) as context:
            CourseCertificate(
                site=self.site, is_active=True, course_id='test_invalid',
                certificate_type=constants.CertificateType.HONOR
            ).full_clean()

        self.assertEqual(context.exception.message_dict, {'course_id': ['Invalid course key.']})


@ddt.ddt
class ProgramCertificateTests(SiteMixin, TestCase):
    """ Tests for the ProgramCertificate model. """

    def test_str(self):
        instance = ProgramCertificateFactory()
        self.assertEqual(str(instance), 'ProgramCertificate: ' + str(instance.program_uuid))

    @ddt.data(
        (True, None),
        (True, 'Test custom credential title'),
        (False, None),
        (False, 'Other very special credential title'),
    )
    @ddt.unpack
    def test_program_details(self, use_org_name, credential_title):
        """ Verify the method returns the details of program associated with the ProgramCertificate. """
        program_certificate = ProgramCertificateFactory(site=self.site, use_org_name=use_org_name,
                                                        title=credential_title)
        program_uuid = program_certificate.program_uuid.hex
        courses = [
            {'key': 'ACMEx/101x'},
            {'key': 'FakeX/101x'},
        ]
        expected = ProgramDetails(
            uuid=program_uuid,
            title='Test Program',
            subtitle='Test Subtitle',
            type='MicroFakers',
            credential_title=credential_title,
            course_count=len(courses),
            organizations=[
                OrganizationDetails(
                    uuid=uuid.uuid4().hex,
                    key='ACMEx',
                    name='ACME University',
                    display_name='ACME University' if use_org_name else 'ACMEx',
                    certificate_logo_image_url='http://example.com/acme.jpg'
                ),
                OrganizationDetails(
                    uuid=uuid.uuid4().hex,
                    key='FakeX',
                    name='Fake University',
                    display_name='Fake University' if use_org_name else 'FakeX',
                    certificate_logo_image_url='http://example.com/fakex.jpg'
                )
            ],
            hours_of_effort=None
        )

        body = {
            'uuid': expected.uuid,
            'title': expected.title,
            'subtitle': expected.subtitle,
            'type': expected.type,
            'authoring_organizations': [
                {
                    'uuid': organization.uuid,
                    'key': organization.key,
                    'name': organization.name,
                    'certificate_logo_image_url': organization.certificate_logo_image_url,

                } for organization in expected.organizations
            ],
            'courses': courses
        }

        with mock.patch.object(SiteConfiguration, 'get_program', return_value=body) as mock_method:
            self.assertEqual(program_certificate.program_details, expected)
            mock_method.assert_called_with(program_certificate.program_uuid)

    def test_get_program_api_data(self):
        """ Verify the method returns data from the Catalog API. """
        program_certificate = ProgramCertificateFactory(site=self.site)
        expected = {
            'uuid': program_certificate.program_uuid.hex
        }

        with mock.patch.object(SiteConfiguration, 'get_program', return_value=expected) as mock_method:
            self.assertEqual(program_certificate.get_program_api_data(), expected)
            mock_method.assert_called_with(program_certificate.program_uuid)


class UserCredentialTests(TestCase):
    def test_revoke(self):
        credential = UserCredentialFactory(status=UserCredential.AWARDED)
        self.assertEqual(credential.status, UserCredential.AWARDED)

        credential.revoke()
        self.assertEqual(credential.status, UserCredential.REVOKED)
