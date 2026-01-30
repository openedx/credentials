import base64
import gzip
from unittest import mock

from django.test import TestCase

from credentials.apps.verifiable_credentials.issuance.models import IssuanceLine
from credentials.apps.verifiable_credentials.issuance.tests.factories import IssuanceLineFactory

from ..status_list import (
    StatusEntrySchema,
    StatusList2021EntryMixin,
    StatusListDataModel,
    StatusListSubjectSchema,
    regenerate_encoded_status_sequence,
)


class StatusListCompositionTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.issuance_line = IssuanceLineFactory.create(status_index=5)

    @mock.patch("credentials.apps.verifiable_credentials.issuance.utils.get_revoked_indices")
    def test_regenerate_encoded_status_sequence(self, mock_get_revoked_indices):
        mock_get_revoked_indices.return_value = [1, 3, 5]
        result = regenerate_encoded_status_sequence("test")
        # Add padding back for urlsafe_b64decode
        padded_result = result + "=" * (-len(result) % 4)
        decoded_data = base64.urlsafe_b64decode(padded_result)
        decompressed_data = gzip.decompress(decoded_data)
        status_list = bytearray(decompressed_data)

        for i in range(5):
            if i in mock_get_revoked_indices.return_value:
                self.assertEqual(status_list[i], 1)
            else:
                self.assertEqual(status_list[i], 0)

    def test_status_list_2021_entry_mixin_get_context(self):
        self.assertEqual(type(StatusList2021EntryMixin.get_context()), list)

    @mock.patch.object(IssuanceLine, "get_status_list_url")
    def test_status_entry_schema_get_id(self, mock_get_status_list_url):
        mock_get_status_list_url.return_value = "test-value"
        issuance_line_id = StatusEntrySchema().get_id(self.issuance_line)
        self.assertEqual(issuance_line_id, "test-value")

    @mock.patch.object(IssuanceLine, "get_status_list_url")
    def test_status_list_subject_schema_get_id(self, mock_get_status_list_url):
        StatusListSubjectSchema().get_id(self.issuance_line)
        mock_get_status_list_url.assert_called_once_with(hash_str="list")

    @mock.patch("credentials.apps.verifiable_credentials.composition.status_list.regenerate_encoded_status_sequence")
    def test_status_list_subject_schema_get_encoded_list(self, mock_regenerate_encoded_status_sequence):
        mock_regenerate_encoded_status_sequence.return_value = ["test-value"]
        encoded_list = StatusListSubjectSchema().get_encoded_list(self.issuance_line)
        self.assertEqual(encoded_list, ["test-value"])

    def test_status_list_data_model_get_context(self):
        self.assertEqual(type(StatusListDataModel.get_context()), list)

    def test_status_list_data_model_get_types(self):
        self.assertEqual(type(StatusListDataModel.get_types()), list)
