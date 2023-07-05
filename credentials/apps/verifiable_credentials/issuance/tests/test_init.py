from django.test import TestCase

from .. import IssuanceException


class IssuanceExceptionTestCase(TestCase):
    def test_issuance_exception(self):
        exception = IssuanceException("Test Details")
        self.assertEqual(str(exception), "Test Details")
