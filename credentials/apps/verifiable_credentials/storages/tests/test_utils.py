from django.test import TestCase

from ..utils import get_storage


class UtilsTestCase(TestCase):
    def test_get_invalid_storage(self):
        invalid_storage_id = "invalid_storage_id"
        storage = get_storage(invalid_storage_id)
        self.assertIsNone(storage)
