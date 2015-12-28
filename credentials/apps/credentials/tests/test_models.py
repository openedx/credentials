"""Test models for credentials service app."""
from django.test import TestCase
from django.contrib.sites.models import Site
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from opaque_keys.edx.locator import CourseLocator

from credentials.apps.credentials import constants
from credentials.apps.credentials.models import (
    CertificateTemplateAsset, CertificateTemplate,
    CourseCertificate, Signatory
)
from credentials.settings.base import MEDIA_ROOT


# pylint: disable=invalid-name
TEST_DATA_ROOT = MEDIA_ROOT + '/test/data/'


class TestSignatory(TestCase):
    """Test Signatory model."""

    def get_image(self, name):
        """Get one of the test images from the test data directory."""
        return ImageFile(open(TEST_DATA_ROOT + name + '.png'))

    # pylint: disable=no-member
    def create_clean(self, file_obj):
        """
        Shortcut to create a Signatory with a specific file.
        """
        Signatory(name='test_signatory', title='Test Signatory', image=file_obj).full_clean()

    # pylint: disable=no-member
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
            'file contents!')).save()
        signatory = Signatory.objects.get(id=1)
        self.assertEqual(
            signatory.image, 'signatories/1/image.jpg'
        )

        # Now replace the asset with another file
        signatory.image = SimpleUploadedFile('image_2.jpg', 'file contents')
        signatory.save()

        signatory = Signatory.objects.get(id=1)
        self.assertEqual(
            signatory.image, 'signatories/1/image_2.jpg'
        )

    def test_unicode_value(self):
        """Test unicode value is correct."""
        signatory = Signatory.objects.create(name='test name', title='test title', image=SimpleUploadedFile(
            'image.jpg',
            'file contents!'))
        self.assertEqual(unicode(signatory), 'test name, test title')


class TestCertificateTemplateAsset(TestCase):
    """
    Test Assets are uploading/saving successfully for CertificateTemplateAsset.
    """

    def test_asset_file_saving(self):
        """
        Verify that asset file is saving with actual name and on correct path.
        """
        certificate_template_asset = CertificateTemplateAsset.objects.create(
            name='test name', asset_file=SimpleUploadedFile('image.jpg', 'file contents!')
        )
        self.assertEqual(
            certificate_template_asset.asset_file, 'certificate_template_assets/1/image.jpg'
        )

        # Now replace the asset with another file
        certificate_template_asset.asset_file = SimpleUploadedFile('image_2.jpg', 'file contents')
        certificate_template_asset.save()

        certificate_template_asset = CertificateTemplateAsset.objects.get(id=1)
        self.assertEqual(
            certificate_template_asset.asset_file, 'certificate_template_assets/1/image_2.jpg'
        )

    def test_unicode_value(self):
        """Test unicode value is correct."""
        CertificateTemplateAsset(name='test name', asset_file=SimpleUploadedFile(
            'picture_1.jpg',
            'file contents!')).save()
        certificate_template_asset = CertificateTemplateAsset.objects.get(id=1)
        self.assertEqual(unicode(certificate_template_asset), 'test name')


class TestCertificateTemplate(TestCase):
    """Test CertificateTemplate model"""

    def test_unicode_value(self):
        """Test unicode value is correct."""
        certificate_template = CertificateTemplate.objects.create(name='test template', content="dummy content")
        self.assertEqual(unicode(certificate_template), 'test template')


class TestCertificates(TestCase):
    """Basic setup for certificate tests."""

    def setUp(self):
        super(TestCertificates, self).setUp()
        self.site = Site.objects.create(domain='test', name='test')
        Signatory(name='test name', title='test title', image=SimpleUploadedFile(
            'picture1.jpg',
            'image contents!')).save()
        self.signatory = Signatory.objects.get(id=1)


class TestCourseCertificate(TestCertificates):
    """Test Course Certificate model."""

    def setUp(self):
        super(TestCourseCertificate, self).setUp()
        self.course_key = CourseLocator(org='test', course='test', run='test')

    # pylint: disable=no-member
    def test_invalid_course_key(self):
        """Test Validation Error occurs for invalid course key."""
        with self.assertRaises(ValidationError) as context:
            CourseCertificate(
                site=self.site, is_active=True, course_id='test_invalid',
                certificate_type=constants.CertificateType.HONOR
            ).full_clean()

        self.assertEqual(context.exception.message_dict, {'course_id': ['Invalid course key.']})
