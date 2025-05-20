import importlib
import sys
import unittest
from unittest import mock


class TestStorageSettings(unittest.TestCase):
    def setUp(self):
        self.module_path = "credentials.settings.base"

    def tearDown(self):
        if self.module_path in sys.modules:
            del sys.modules[self.module_path]

    @mock.patch("django.VERSION", new=(4, 2))
    def test_django_42_or_higher(self):
        if self.module_path in sys.modules:
            del sys.modules[self.module_path]

        imported = importlib.import_module(self.module_path)

        # Verify correct settings for Django 4.2+
        self.assertTrue(hasattr(imported, "STORAGES"))
        self.assertEqual(imported.STORAGES["default"]["BACKEND"], "django.core.files.storage.FileSystemStorage")
        self.assertEqual(
            imported.STORAGES["staticfiles"]["BACKEND"], "django.contrib.staticfiles.storage.StaticFilesStorage"
        )
        self.assertFalse(hasattr(imported, "DEFAULT_FILE_STORAGE"))
        self.assertFalse(hasattr(imported, "STATICFILES_STORAGE"))

    @mock.patch("django.VERSION", new=(4, 1))
    def test_django_below_42(self):
        if self.module_path in sys.modules:
            del sys.modules[self.module_path]

        imported = importlib.import_module(self.module_path)

        # Verify correct settings for Django < 4.2
        self.assertTrue(hasattr(imported, "DEFAULT_FILE_STORAGE"))
        self.assertTrue(hasattr(imported, "STATICFILES_STORAGE"))
        self.assertEqual(imported.DEFAULT_FILE_STORAGE, "django.core.files.storage.FileSystemStorage")
        self.assertEqual(imported.STATICFILES_STORAGE, "django.contrib.staticfiles.storage.StaticFilesStorage")
        self.assertFalse(hasattr(imported, "STORAGES"))
