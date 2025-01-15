from unittest import mock

import faker
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from credentials.apps.badges.issuers import CredlyBadgeTemplateIssuer
from credentials.apps.badges.models import CredlyBadge, CredlyBadgeTemplate, CredlyOrganization
from credentials.apps.badges.signals.signals import BADGE_PROGRESS_COMPLETE, BADGE_PROGRESS_INCOMPLETE


class BadgeSignalReceiverTestCase(TestCase):
    def setUp(self):
        # Create a test badge template
        fake = faker.Faker()
        credly_organization = CredlyOrganization.objects.create(
            uuid=fake.uuid4(), api_key=fake.uuid4(), name=fake.word()
        )
        self.badge_template = CredlyBadgeTemplate.objects.create(
            name="test", site_id=1, organization=credly_organization
        )

    def test_progression_signal_emission_and_receiver_execution(self):
        # Emit the signal
        with mock.patch("credentials.apps.badges.issuers.notify_badge_awarded"):
            with mock.patch.object(CredlyBadgeTemplateIssuer, "issue_credly_badge"):
                BADGE_PROGRESS_COMPLETE.send(
                    sender=self,
                    username="test_user",
                    badge_template_id=self.badge_template.id,
                    origin=self.badge_template.origin,
                )

        # UserCredential object
        user_credential = CredlyBadge.objects.filter(
            username="test_user",
            credential_content_type=ContentType.objects.get_for_model(self.badge_template),
            credential_id=self.badge_template.id,
        )

        # Check if user credential is created
        self.assertTrue(user_credential.exists())

        # Check if user credential status is 'awarded'
        self.assertEqual(user_credential[0].status, "awarded")

    def test_regression_signal_emission_and_receiver_execution(self):
        # Emit the signal
        with mock.patch("credentials.apps.badges.issuers.notify_badge_revoked"):
            with mock.patch.object(CredlyBadgeTemplateIssuer, "revoke_credly_badge"):
                BADGE_PROGRESS_INCOMPLETE.send(
                    sender=self,
                    username="test_user",
                    badge_template_id=self.badge_template.id,
                    origin=self.badge_template.origin,
                )

        # UserCredential object
        user_credential = CredlyBadge.objects.filter(
            username="test_user",
            credential_content_type=ContentType.objects.get_for_model(self.badge_template),
            credential_id=self.badge_template.id,
        )

        # Check if user credential is created
        self.assertTrue(user_credential.exists())

        # Check if user credential status is 'revoked'
        self.assertEqual(user_credential[0].status, "revoked")
