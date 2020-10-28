from unittest import mock

from django.test import TestCase

from credentials.apps.credentials.templatetags.html import month


@mock.patch('credentials.apps.credentials.templatetags.html.date')
@mock.patch('credentials.apps.credentials.templatetags.html.get_language')
class TestTemplateTagsHtmlMonth(TestCase):
    def test_spanish_month_lower(self, mock_get_language, mock_date):
        """
        Verify edxdate lower cases Spanish months
        """
        mock_date.return_value = 'Test'

        # French version (same case)
        mock_get_language.return_value = 'fr-FR'
        self.assertEqual('Test', month(None))

        # Spanish version (lowercases)
        mock_get_language.return_value = 'es-MX'
        self.assertEqual('test', month(None))

    def test_no_language(self, mock_get_language, mock_date):
        """
        Verify month gracefully handles no defined language
        """
        mock_date.return_value = 'Test'
        mock_get_language.return_value = None
        self.assertEqual('Test', month(None))
