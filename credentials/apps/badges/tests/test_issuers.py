from unittest import mock
from unittest.mock import patch

import faker
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from credentials.apps.badges.accredible.api_client import AccredibleAPIClient
from credentials.apps.badges.credly.api_client import CredlyAPIClient
from credentials.apps.badges.exceptions import BadgeProviderError
from credentials.apps.badges.issuers import AccredibleBadgeTemplateIssuer, CredlyBadgeTemplateIssuer
from credentials.apps.badges.models import (
    AccredibleAPIConfig,
    AccredibleBadge,
    AccredibleGroup,
    CredlyBadge,
    CredlyBadgeTemplate,
    CredlyOrganization,
)
from credentials.apps.credentials.constants import UserCredentialStatus


User = get_user_model()


class CredlyBadgeTemplateIssuerTestCase(TestCase):
    issued_credential_type = CredlyBadgeTemplate
    issued_user_credential_type = CredlyBadge
    issuer = CredlyBadgeTemplateIssuer

    def setUp(self):
        # Create a test badge template
        self.fake = faker.Faker()
        credly_organization = CredlyOrganization.objects.create(
            uuid=self.fake.uuid4(), api_key=self.fake.uuid4(), name=self.fake.word()
        )
        self.badge_template = self.issued_credential_type.objects.create(
            origin=self.issued_credential_type.ORIGIN,
            site_id=1,
            uuid=self.fake.uuid4(),
            name=self.fake.word(),
            state="active",
            organization=credly_organization,
        )
        User.objects.create_user(username="test_user", email="test_email@fff.com", password="test_password")

    def _perform_request(self, method, endpoint, data=None):  # pylint: disable=unused-argument
        fake = faker.Faker()
        return {"data": {"id": fake.uuid4(), "state": "issued"}}

    def test_create_user_credential_with_status_awared(self):
        # Call create_user_credential with valid arguments
        with mock.patch("credentials.apps.badges.issuers.notify_badge_awarded") as mock_notify_badge_awarded:

            with mock.patch.object(self.issuer, "issue_credly_badge") as mock_issue_credly_badge:
                self.issuer().award(credential_id=self.badge_template.id, username="test_user")

            mock_notify_badge_awarded.assert_called_once()
            mock_issue_credly_badge.assert_called_once()

            # Check if user credential is created
            self.assertTrue(
                self.issued_user_credential_type.objects.filter(
                    username="test_user",
                    credential_content_type=ContentType.objects.get_for_model(self.badge_template),
                    credential_id=self.badge_template.id,
                ).exists()
            )

    def test_create_user_credential_with_status_revoked(self):
        # Call create_user_credential with valid arguments
        self.issued_user_credential_type.objects.create(
            username="test_user",
            credential_content_type=ContentType.objects.get_for_model(self.badge_template),
            credential_id=self.badge_template.id,
            state=CredlyBadge.STATES.pending,
            uuid=self.fake.uuid4(),
            external_uuid=self.fake.uuid4(),
        )

        with mock.patch("credentials.apps.badges.issuers.notify_badge_revoked") as mock_notify_badge_revoked:
            with mock.patch.object(self.issuer, "revoke_credly_badge") as mock_revoke_credly_badge:
                self.issuer().revoke(self.badge_template.id, "test_user")

            mock_revoke_credly_badge.assert_called_once()
            mock_notify_badge_revoked.assert_called_once()

            # Check if user credential is created
            self.assertTrue(
                self.issued_user_credential_type.objects.filter(
                    username="test_user",
                    credential_content_type=ContentType.objects.get_for_model(self.badge_template),
                    credential_id=self.badge_template.id,
                    status=UserCredentialStatus.REVOKED,
                ).exists()
            )

    @patch.object(CredlyAPIClient, "perform_request", _perform_request)
    def test_issue_credly_badge(self):
        # Create a test user credential
        user_credential = self.issued_user_credential_type.objects.create(
            username="test_user",
            credential_content_type=ContentType.objects.get_for_model(self.badge_template),
            credential_id=self.badge_template.id,
            state=CredlyBadge.STATES.pending,
            uuid=self.fake.uuid4(),
            external_uuid=self.fake.uuid4(),
        )

        # Call the issue_credly_badge method
        self.issuer().issue_credly_badge(user_credential=user_credential)

        # Check if the user credential is updated with the external UUID and state
        self.assertIsNotNone(user_credential.external_uuid)
        self.assertEqual(user_credential.state, "issued")

        # Check if the user credential is saved
        user_credential.refresh_from_db()
        self.assertIsNotNone(user_credential.external_uuid)
        self.assertEqual(user_credential.state, "issued")

    def test_issue_credly_badge_with_error(self):
        # Create a test user credential
        user_credential = self.issued_user_credential_type.objects.create(
            username="test_user",
            credential_content_type=ContentType.objects.get_for_model(self.badge_template),
            credential_id=self.badge_template.id,
            state=CredlyBadge.STATES.pending,
            uuid=self.fake.uuid4(),
            external_uuid=self.fake.uuid4(),
        )

        # Mock the CredlyAPIClient and its issue_badge method to raise CredlyAPIError
        with mock.patch("credentials.apps.badges.credly.api_client.CredlyAPIClient") as mock_credly_api_client:
            mock_issue_badge = mock_credly_api_client.return_value.issue_badge
            mock_issue_badge.side_effect = BadgeProviderError

            # Call the issue_credly_badge method and expect CredlyAPIError to be raised
            with self.assertRaises(BadgeProviderError):
                self.issuer().issue_credly_badge(user_credential=user_credential)

            # Check if the user credential state is updated to "error"
            user_credential.refresh_from_db()
            self.assertEqual(user_credential.state, "error")

    @patch.object(CredlyAPIClient, "revoke_badge")
    def test_revoke_credly_badge_success(self, mock_revoke_badge):
        user_credential = self.issued_user_credential_type.objects.create(
            username="test_user",
            credential_content_type=ContentType.objects.get_for_model(self.badge_template),
            credential_id=self.badge_template.id,
            state=CredlyBadge.STATES.accepted,
            uuid=self.fake.uuid4(),
            external_uuid=self.fake.uuid4(),
        )

        mock_revoke_badge.return_value = {"data": {"state": "revoked"}}

        self.issuer().revoke_credly_badge(self.badge_template.id, user_credential)

        user_credential.refresh_from_db()
        self.assertEqual(user_credential.state, "revoked")

    @patch.object(CredlyAPIClient, "revoke_badge", side_effect=BadgeProviderError("Revocation failed"))
    def test_revoke_credly_badge_failure(self, mock_revoke_badge):  # pylint: disable=unused-argument
        user_credential = self.issued_user_credential_type.objects.create(
            username="test_user",
            credential_content_type=ContentType.objects.get_for_model(self.badge_template),
            credential_id=self.badge_template.id,
            state=CredlyBadge.STATES.accepted,
            uuid=self.fake.uuid4(),
            external_uuid=self.fake.uuid4(),
        )

        with self.assertRaises(BadgeProviderError):
            self.issuer().revoke_credly_badge(self.badge_template.id, user_credential)

        user_credential.refresh_from_db()
        self.assertEqual(user_credential.state, "error")


class AccredibleBadgeTemplateIssuerTestCase(TestCase):
    issued_credential_type = AccredibleGroup
    issued_user_credential_type = AccredibleBadge
    issuer = AccredibleBadgeTemplateIssuer

    def setUp(self):
        self.fake = faker.Faker()
        self.accredible_api_config = AccredibleAPIConfig.objects.create(
            api_key=self.fake.uuid4(), name=self.fake.word()
        )
        self.group = self.issued_credential_type.objects.create(
            origin=self.issued_credential_type.ORIGIN,
            site_id=1,
            uuid=self.fake.uuid4(),
            name=self.fake.word(),
            state="active",
            api_config=self.accredible_api_config,
        )
        User.objects.create_user(username="test_user", email="test_email@example.com", password="test_password")

    def _perform_request(self, method, endpoint, data=None):  # pylint: disable=unused-argument
        return {"credential": {"id": 123}}

    def test_create_user_credential_awarded(self):
        with mock.patch("credentials.apps.badges.issuers.notify_badge_awarded") as mock_notify_badge_awarded:
            with mock.patch.object(self.issuer, "issue_accredible_badge") as mock_issue_accredible_badge:
                self.issuer().award(credential_id=self.group.id, username="test_user")

            mock_notify_badge_awarded.assert_called_once()
            mock_issue_accredible_badge.assert_called_once()

            self.assertTrue(
                self.issued_user_credential_type.objects.filter(
                    username="test_user",
                    credential_content_type=ContentType.objects.get_for_model(self.group),
                    credential_id=self.group.id,
                ).exists()
            )

    def test_create_user_credential_revoked(self):
        self.issued_user_credential_type.objects.create(
            username="test_user",
            credential_content_type=ContentType.objects.get_for_model(self.group),
            credential_id=self.group.id,
            state=AccredibleBadge.STATES.accepted,
            uuid=self.fake.uuid4(),
            external_id=123,
        )

        with mock.patch("credentials.apps.badges.issuers.notify_badge_revoked") as mock_notify_badge_revoked:
            with mock.patch.object(self.issuer, "revoke_accredible_badge") as mock_revoke_accredible_badge:
                self.issuer().revoke(self.group.id, "test_user")

            mock_revoke_accredible_badge.assert_called_once()
            mock_notify_badge_revoked.assert_called_once()

            self.assertTrue(
                self.issued_user_credential_type.objects.filter(
                    username="test_user",
                    credential_content_type=ContentType.objects.get_for_model(self.group),
                    credential_id=self.group.id,
                    status=UserCredentialStatus.REVOKED,
                ).exists()
            )

    @patch.object(AccredibleAPIClient, "perform_request", _perform_request)
    def test_issue_accredible_badge(self):
        user_credential = self.issued_user_credential_type.objects.create(
            username="test_user",
            credential_content_type=ContentType.objects.get_for_model(self.group),
            credential_id=self.group.id,
            state=AccredibleBadge.STATES.accepted,
            uuid=self.fake.uuid4(),
            external_id=123,
        )

        self.issuer().issue_accredible_badge(user_credential=user_credential)

        self.assertIsNotNone(user_credential.external_id)
        self.assertEqual(user_credential.state, AccredibleBadge.STATES.accepted)

        user_credential.refresh_from_db()
        self.assertIsNotNone(user_credential.external_id)
        self.assertEqual(user_credential.state, AccredibleBadge.STATES.accepted)

    def test_issue_accredible_badge_with_error(self):
        user_credential = self.issued_user_credential_type.objects.create(
            username="test_user",
            credential_content_type=ContentType.objects.get_for_model(self.group),
            credential_id=self.group.id,
            state=AccredibleBadge.STATES.accepted,
            uuid=self.fake.uuid4(),
            external_id=123,
        )

        with mock.patch(
            "credentials.apps.badges.accredible.api_client.AccredibleAPIClient"
        ) as mock_accredible_api_client:
            mock_issue_badge = mock_accredible_api_client.return_value.issue_badge
            mock_issue_badge.side_effect = BadgeProviderError

            with self.assertRaises(BadgeProviderError):
                self.issuer().issue_accredible_badge(user_credential=user_credential)

            user_credential.refresh_from_db()
            self.assertEqual(user_credential.state, "error")

    @patch.object(AccredibleAPIClient, "revoke_badge")
    def test_revoke_accredible_badge_success(self, mock_revoke_badge):
        user_credential = self.issued_user_credential_type.objects.create(
            username="test_user",
            credential_content_type=ContentType.objects.get_for_model(self.group),
            credential_id=self.group.id,
            state=AccredibleBadge.STATES.accepted,
            uuid=self.fake.uuid4(),
            external_id=123,
        )

        mock_revoke_badge.return_value = {"credential": {"id": 123}}

        self.issuer().revoke_accredible_badge(self.group.id, user_credential)

        user_credential.refresh_from_db()
        self.assertEqual(user_credential.state, "expired")

    @patch.object(AccredibleAPIClient, "revoke_badge", side_effect=BadgeProviderError("Revocation failed"))
    def test_revoke_accredible_badge_failure(self, mock_revoke_badge):  # pylint: disable=unused-argument
        user_credential = self.issued_user_credential_type.objects.create(
            username="test_user",
            credential_content_type=ContentType.objects.get_for_model(self.group),
            credential_id=self.group.id,
            state=AccredibleBadge.STATES.accepted,
            uuid=self.fake.uuid4(),
            external_id=123,
        )

        with self.assertRaises(BadgeProviderError):
            self.issuer().revoke_accredible_badge(self.group.id, user_credential)

        user_credential.refresh_from_db()
        self.assertEqual(user_credential.state, "error")
