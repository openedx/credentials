"""
Tests for s3 library customization utilities.
"""

from django.test import TestCase
import mock

from credentials.apps.core.s3utils import MediaS3BotoStorage, StaticS3BotoStorage


class TestS3NoSecurityTokenConnection(TestCase):
    """
    Tests for the custom s3 connection.
    """

    def test_no_security_token(self):
        """
        Ensure the querystring-inhibiting workaround takes effect with our
        custom S3 storage drivers.
        """
        # note that the default value for the security token is None in a non-AWS env;
        # therefore our manually-set empty string indicates that the override is working

        with mock.patch('boto.auth.get_auth_handler'):  # prevents errors running in TravisCI
            media_storage = MediaS3BotoStorage()
            self.assertEqual(media_storage.connection.provider.security_token, "")

            static_storage = StaticS3BotoStorage()
            self.assertEqual(static_storage.connection.provider.security_token, "")
