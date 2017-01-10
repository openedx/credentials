"""Test models for credentials service app."""

from __future__ import unicode_literals

import uuid

import ddt
import responses
from django.core.exceptions import ValidationError
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from opaque_keys.edx.locator import CourseLocator

from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials import constants
from credentials.apps.credentials.models import (
    CertificateTemplateAsset, CertificateTemplate, CourseCertificate, Signatory, ProgramDetails, OrganizationDetails,
    UserCredential
)
from credentials.apps.credentials.tests.factories import (
    ProgramCertificateFactory, SignatoryFactory, UserCredentialFactory
)
from credentials.settings.base import MEDIA_ROOT

# pylint: disable=invalid-name,no-member
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
        Signatory(name='test name', title='Test Signatory', image=SimpleUploadedFile(
            'image.jpg',
            str('file contents!'))).save()
        signatory = Signatory.objects.get(id=1)
        self.assertEqual(
            signatory.image, 'signatories/1/image.jpg'
        )

        # Now replace the asset with another file
        signatory.image = SimpleUploadedFile('image_2.jpg', str('file contents'))
        signatory.save()

        signatory = Signatory.objects.get(id=1)
        self.assertEqual(
            signatory.image, 'signatories/1/image_2.jpg'
        )

    def test_unicode(self):
        """ Verify the method serializes the Signatory's name and title. """
        signatory = SignatoryFactory()
        self.assertEqual(unicode(signatory), signatory.name + ', ' + signatory.title)


class CertificateTemplateAssetTests(TestCase):
    """
    Test Assets are uploading/saving successfully for CertificateTemplateAsset.
    """

    def test_asset_file_saving(self):
        """
        Verify that asset file is saving with actual name and on correct path.
        """
        certificate_template_asset = CertificateTemplateAsset.objects.create(
            name='test name', asset_file=SimpleUploadedFile('image.jpg', str('file contents!'))
        )
        self.assertEqual(
            certificate_template_asset.asset_file, 'certificate_template_assets/1/image.jpg'
        )

        # Now replace the asset with another file
        certificate_template_asset.asset_file = SimpleUploadedFile('image_2.jpg', str('file contents'))
        certificate_template_asset.save()

        certificate_template_asset = CertificateTemplateAsset.objects.get(id=certificate_template_asset.id)
        self.assertEqual(
            certificate_template_asset.asset_file, 'certificate_template_assets/1/image_2.jpg'
        )

    def test_unicode_value(self):
        """Test unicode value is correct."""
        instance = CertificateTemplateAsset(name='test name')
        self.assertEqual(unicode(instance), instance.name)


class CertificateTemplateTests(TestCase):
    """Test CertificateTemplate model"""

    def test_unicode(self):
        """Test unicode value is correct."""
        certificate_template = CertificateTemplate.objects.create(name='test template', content="dummy content")
        self.assertEqual(unicode(certificate_template), 'test template')


class CourseCertificateTests(SiteMixin, TestCase):
    """Test Course Certificate model."""

    def setUp(self):
        super(CourseCertificateTests, self).setUp()
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

        instance = ProgramCertificateFactory(program_uuid=None)
        self.assertEqual(str(instance), 'ProgramCertificate: ' + str(instance.program_id))

    @ddt.data(True, False)
    @responses.activate
    def test_program_details(self, use_org_name):
        """ Verify the method returns the details of program associated with the ProgramCertificate. """
        program_certificate = ProgramCertificateFactory(site=self.site, use_org_name=use_org_name)
        program_uuid = program_certificate.program_uuid.hex
        courses = [
            {'key': 'ACMEx/101x'},
            {'key': 'FakeX/101x'},
        ]
        expected = ProgramDetails(
            uuid=program_uuid,
            title='Test Program',
            type='MicroFakers',
            course_count=len(courses),
            organizations=[
                OrganizationDetails(
                    uuid=uuid.uuid4().hex,
                    key='ACMEx',
                    name='ACME University',
                    display_name='ACME University' if use_org_name else 'ACMEx',
                    logo_image_url='http://example.com/acme.jpg'
                ),
                OrganizationDetails(
                    uuid=uuid.uuid4().hex,
                    key='FakeX',
                    name='Fake University',
                    display_name='Fake University' if use_org_name else 'FakeX',
                    logo_image_url='http://example.com/fakex.jpg'
                )
            ]
        )

        program_endpoint = 'programs/{uuid}/'.format(uuid=program_uuid)
        body = {
            'uuid': expected.uuid,
            'title': expected.title,
            'type': expected.type,
            'authoring_organizations': [
                {
                    'uuid': organization.uuid,
                    'key': organization.key,
                    'name': organization.name,
                    'logo_image_url': organization.logo_image_url,

                } for organization in expected.organizations
            ],
            'courses': courses
        }

        self.mock_access_token_response()
        self.mock_catalog_api_response(program_endpoint, body)

        self.assertEqual(program_certificate.program_details, expected)

    @responses.activate
    def test_get_program_api_data(self):
        """ Verify the method returns data from the Catalog API. """
        program_certificate = ProgramCertificateFactory(site=self.site)
        program_uuid = program_certificate.program_uuid.hex

        program_endpoint = 'programs/{uuid}/'.format(uuid=program_uuid)
        body = {
            'uuid': program_uuid,
            'title': 'A Fake Program',
            'type': 'fake',
            'authoring_organizations': [
                {
                    'uuid': uuid.uuid4().hex,
                    'key': 'FakeX',
                    'name': 'Fake University',
                    'logo_image_url': 'https://static.fake.edu/logo.png',

                }
            ],
            'courses': []
        }

        self.mock_access_token_response()
        self.mock_catalog_api_response(program_endpoint, body)

        self.assertEqual(program_certificate.get_program_api_data(), body)

        # Verify the data is cached
        responses.reset()
        self.assertEqual(program_certificate.get_program_api_data(), body)


class UserCredentialTests(TestCase):
    def test_revoke(self):
        credential = UserCredentialFactory(status=UserCredential.AWARDED)
        self.assertEqual(credential.status, UserCredential.AWARDED)

        credential.revoke()
        self.assertEqual(credential.status, UserCredential.REVOKED)
