from unittest import mock

import faker
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from credentials.apps.credentials.constants import UserCredentialStatus

from ..issuers import CredlyBadgeTemplateIssuer
from ..models import CredlyBadge, CredlyBadgeTemplate, CredlyOrganization


class CredlyBadgeTemplateIssuer(TestCase):
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
