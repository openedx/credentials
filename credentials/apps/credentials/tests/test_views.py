"""
Tests for credentials rendering views.
"""
from __future__ import unicode_literals
import uuid

from django.test import TestCase
from django.core.urlresolvers import reverse
from credentials.apps.api.tests import factories
from credentials.apps.credentials.models import UserCredential


class RenderCredentialPageTests(TestCase):
    """ Tests for credential rendering view. """

    def setUp(self):
        super(RenderCredentialPageTests, self).setUp()

        self.program_certificate = factories.ProgramCertificateFactory.create(template=None)
        self.user_credential = factories.UserCredentialFactory.create(
            credential=self.program_certificate
        )
        self.username = 'test-user'

    def test_get_cert_with_awarded_status(self):
        """ Verify that view render certificate and returns 200 with valid uuid and status
        is awarded.
        """
        path = reverse('credentials:render', kwargs={'uuid': self.user_credential.uuid.hex})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self._assert_user_credential_with_default_template(response, self.user_credential)

    def test_get_cert_with_revoked_status(self):
        """ Verify that view render certificate and returns 404 with valid uuid and status
        is revoked.
        """
        self.user_credential.status = UserCredential.REVOKED
        self.user_credential.save()
        path = reverse('credentials:render', kwargs={'uuid': self.user_credential.uuid.hex})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def test_get_cert_with_invalid_uuid(self):
        """ Verify that view returns 404 with invalid uuid."""
        path = reverse('credentials:render', kwargs={'uuid': uuid.uuid4().hex})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def test_get_cert_with_invalid_content_type_model(self):
        """ Verify that view returns 404 with course certificate content type model."""
        course_certificate = factories.CourseCertificateFactory.create(template=None)
        user_credential = factories.UserCredentialFactory.create(
            credential=course_certificate
        )

        path = reverse('credentials:render', kwargs={'uuid': user_credential.uuid.hex})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def test_get_cert_invalid_credential_id(self):
        """ Verify that view will return 404 if credential ID is invalid."""
        self.user_credential.credential_id = 1000
        self.user_credential.save()
        path = reverse('credentials:render', kwargs={'uuid': self.user_credential.uuid.hex})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def _assert_user_credential_with_default_template(self, response, user_credential):
        """ Verify the default template has the data. """
        self.assertContains(response, user_credential.username)
        self.assertContains(response, self.user_credential.uuid)

        issued_data = '{month} {day}, {year}'.format(
            month=user_credential.modified.strftime("%B"),
            day=user_credential.modified.day,
            year=user_credential.modified.year
        )
        self.assertContains(response, issued_data)

        self.assertContains(response, "You worked hard to earn your XSeries certificate from")
        self.assertContains(response, 'An edX XSeries certificate signifies')
        self.assertContains(response, 'For tips and tricks on printing your certificate')
        self.assertContains(response, 'edX is a non-profit online')
        self.assertContains(response, 'All rights reserved except where noted')

    def test_get_cert_with_credential_template(self):
        """ Verify that if credential have template then view will render certificate
        with its own template successfully.
        """
        template = factories.CertificateTemplateFactory.create()
        program_cert = factories.ProgramCertificateFactory(template=template)
        user_credential = factories.UserCredentialFactory.create(credential=program_cert, uuid=uuid.uuid4().hex)
        path = reverse('credentials:render', kwargs={'uuid': user_credential.uuid})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
