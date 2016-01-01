"""
Tests for credentials rendering views.
"""
from __future__ import unicode_literals
import uuid

from django.test import TestCase
from django.core.urlresolvers import reverse


class RenderCredentialPageTests(TestCase):
    """ Tests for credential rendering view. """

    def test_get_valid_uuid(self):
        """
        Test certificate page accessibility. Page will return 200 if uuid is valid.
        """
        path = reverse('credentials:render', kwargs={
            'uuid': uuid.uuid4().hex,
        })
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
