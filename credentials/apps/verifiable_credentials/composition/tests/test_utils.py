from django.test import TestCase

from ..open_badges import OpenBadgesDataModel
from ..status_list import StatusListDataModel
from ..utils import get_available_data_models, get_data_model, get_data_models
from ..verifiable_credentials import VerifiableCredentialsDataModel


class UtilsTestCase(TestCase):
    def test_get_available_data_models(self):
        result = get_available_data_models()
        expected = [VerifiableCredentialsDataModel, OpenBadgesDataModel]
        self.assertEqual(result, expected)

    def test_get_data_models(self):
        result = get_data_models()
        expected = [VerifiableCredentialsDataModel, OpenBadgesDataModel, StatusListDataModel]
        self.assertEqual(result, expected)

    def test_get_data_model_existing_model_id(self):
        result = get_data_model("vc")
        self.assertEqual(result, VerifiableCredentialsDataModel)

    def test_get_data_model_non_existing_model_id(self):
        result = get_data_model("non_existing_model")
        self.assertEqual(result, None)
