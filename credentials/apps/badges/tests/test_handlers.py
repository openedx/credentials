"""Tests for the badge completion signal handler and issuance restrictions."""

from unittest import mock

from django.test import TestCase

from credentials.apps.badges.models import AccredibleGroup, CredlyBadgeTemplate
from credentials.apps.badges.signals.signals import BADGE_PROGRESS_COMPLETE

HANDLERS_MODULE = "credentials.apps.badges.signals.handlers"


class HandleBadgeCompletionRestrictionsTestCase(TestCase):
    """
    Tests for `handle_badge_completion` with badge issuance restrictions.
    """

    def setUp(self):
        super().setUp()
        self.progress = mock.Mock()

        patchers = {
            "progress_model": mock.patch(f"{HANDLERS_MODULE}.BadgeProgress"),
            "is_allowed": mock.patch(f"{HANDLERS_MODULE}.is_badge_issuance_allowed"),
            "credly_issuer": mock.patch(f"{HANDLERS_MODULE}.CredlyBadgeTemplateIssuer"),
            "accredible_issuer": mock.patch(f"{HANDLERS_MODULE}.AccredibleBadgeTemplateIssuer"),
        }
        self.mocks = {}
        for name, patcher in patchers.items():
            self.mocks[name] = patcher.start()
            self.addCleanup(patcher.stop)

        self.mocks["progress_model"].for_user.return_value = self.progress

    def _send(self, origin):
        BADGE_PROGRESS_COMPLETE.send(
            sender=self,
            username="test_user",
            badge_template_id=1,
            origin=origin,
        )

    def test_credly_badge_is_awarded_when_issuance_is_allowed(self):
        self.mocks["is_allowed"].return_value = True

        self._send(CredlyBadgeTemplate.ORIGIN)

        self.mocks["progress_model"].for_user.assert_called_once_with(username="test_user", template_id=1)
        self.mocks["is_allowed"].assert_called_once_with(
            username="test_user",
            badge_template_id=1,
            progress=self.progress,
        )
        self.mocks["credly_issuer"].return_value.award.assert_called_once_with(
            username="test_user",
            credential_id=1,
        )

    def test_credly_badge_is_not_awarded_when_issuance_is_restricted(self):
        self.mocks["is_allowed"].return_value = False

        self._send(CredlyBadgeTemplate.ORIGIN)

        self.mocks["is_allowed"].assert_called_once()
        self.mocks["credly_issuer"].return_value.award.assert_not_called()

    def test_accredible_badge_skips_restriction_check(self):
        self._send(AccredibleGroup.ORIGIN)

        self.mocks["is_allowed"].assert_not_called()
        self.mocks["accredible_issuer"].return_value.award.assert_called_once_with(
            username="test_user",
            credential_id=1,
        )
        self.mocks["credly_issuer"].return_value.award.assert_not_called()
