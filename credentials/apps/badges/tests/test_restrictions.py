"""Tests for badge issuance restriction checks."""

from types import SimpleNamespace
from unittest import mock

import requests
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase, override_settings

from credentials.apps.badges.processing.restrictions import is_badge_issuance_allowed

RESTRICTIONS_MODULE = "credentials.apps.badges.processing.restrictions"
API_URL = "https://example.com/api/v1/restrictions/"
FLAG_NAME = "allow_badges"
CCX_ID = "ccx-v1:ORG+COURSE+RUN+ccx@1"

ENABLED_SETTINGS = {
    "BADGES_ENABLE_ISSUANCE_RESTRICTIONS": True,
    "BADGES_ISSUANCE_RESTRICTIONS_API_URL": API_URL,
    "BADGES_ISSUANCE_RESTRICTIONS_FLAG_NAME": FLAG_NAME,
}


def build_progress(*course_keys):
    """
    Build a fake BadgeProgress exposing the given fulfillment course keys.
    """
    fulfillments = [SimpleNamespace(course_key=course_key) for course_key in course_keys]
    return SimpleNamespace(fulfillment_set=SimpleNamespace(all=lambda: fulfillments))


def build_response(status_code=200, json_data=None, json_error=False):
    """
    Build a fake API response.
    """
    response = mock.Mock()
    response.status_code = status_code
    if json_error:
        response.json.side_effect = ValueError("invalid json")
    else:
        response.json.return_value = json_data
    return response


class IsBadgeIssuanceAllowedTestCase(TestCase):
    """
    Tests for `is_badge_issuance_allowed`.
    """

    def setUp(self):
        super().setUp()
        self.api_client = mock.Mock()

        template_patcher = mock.patch(f"{RESTRICTIONS_MODULE}.CredlyBadgeTemplate")
        site_config_patcher = mock.patch(f"{RESTRICTIONS_MODULE}.SiteConfiguration")
        self.template_mock = template_patcher.start()
        self.site_config_mock = site_config_patcher.start()
        self.addCleanup(template_patcher.stop)
        self.addCleanup(site_config_patcher.stop)

        self.template_mock.objects.get.return_value = SimpleNamespace(site="site")
        self.site_config_mock.objects.get.return_value = SimpleNamespace(api_client=self.api_client)

    def _check(self, progress):
        return is_badge_issuance_allowed(
            username="test_user",
            badge_template_id=1,
            progress=progress,
        )

    def test_allowed_when_feature_is_not_configured(self):
        """
        The feature is disabled by default: no setting means no external call.
        """
        self.assertTrue(self._check(build_progress(CCX_ID)))
        self.api_client.get.assert_not_called()

    @override_settings(BADGES_ENABLE_ISSUANCE_RESTRICTIONS=False)
    def test_allowed_when_feature_is_disabled(self):
        self.assertTrue(self._check(build_progress(CCX_ID)))
        self.api_client.get.assert_not_called()

    @override_settings(**ENABLED_SETTINGS)
    def test_allowed_when_progress_is_missing(self):
        self.assertTrue(self._check(None))
        self.api_client.get.assert_not_called()

    @override_settings(**ENABLED_SETTINGS)
    def test_allowed_when_badge_template_does_not_exist(self):
        self.template_mock.objects.get.side_effect = ObjectDoesNotExist

        self.assertTrue(self._check(build_progress(CCX_ID)))
        self.api_client.get.assert_not_called()

    @override_settings(**ENABLED_SETTINGS)
    def test_allowed_when_site_configuration_does_not_exist(self):
        self.site_config_mock.objects.get.side_effect = ObjectDoesNotExist

        self.assertTrue(self._check(build_progress(CCX_ID)))
        self.api_client.get.assert_not_called()

    @override_settings(**ENABLED_SETTINGS)
    def test_allowed_when_there_are_no_fulfillments(self):
        self.assertTrue(self._check(build_progress()))
        self.api_client.get.assert_not_called()

    @override_settings(**ENABLED_SETTINGS)
    def test_fulfillments_without_course_key_are_skipped(self):
        self.assertTrue(self._check(build_progress(None, "")))
        self.api_client.get.assert_not_called()

    @override_settings(**ENABLED_SETTINGS)
    def test_api_is_called_with_course_key(self):
        self.api_client.get.return_value = build_response(
            json_data={"results": [{"ccx_id": CCX_ID, FLAG_NAME: True}]},
        )

        self.assertTrue(self._check(build_progress(CCX_ID)))
        self.api_client.get.assert_called_once_with(
            API_URL,
            params={"ccx_id": CCX_ID},
            timeout=5,
        )

    @override_settings(**ENABLED_SETTINGS)
    def test_blocked_when_flag_is_false(self):
        self.api_client.get.return_value = build_response(
            json_data={"results": [{"ccx_id": CCX_ID, FLAG_NAME: False}]},
        )

        self.assertFalse(self._check(build_progress(CCX_ID)))

    @override_settings(**ENABLED_SETTINGS)
    def test_blocked_if_any_fulfillment_is_restricted(self):
        other_ccx_id = "ccx-v1:ORG+OTHER+RUN+ccx@2"
        self.api_client.get.side_effect = [
            build_response(json_data={"results": [{"ccx_id": CCX_ID, FLAG_NAME: True}]}),
            build_response(json_data={"results": [{"ccx_id": other_ccx_id, FLAG_NAME: False}]}),
        ]

        self.assertFalse(self._check(build_progress(CCX_ID, other_ccx_id)))
        self.assertEqual(self.api_client.get.call_count, 2)

    @override_settings(**ENABLED_SETTINGS)
    def test_allowed_when_all_fulfillments_are_allowed(self):
        other_ccx_id = "ccx-v1:ORG+OTHER+RUN+ccx@2"
        self.api_client.get.side_effect = [
            build_response(json_data={"results": [{"ccx_id": CCX_ID, FLAG_NAME: True}]}),
            build_response(json_data={"results": [{"ccx_id": other_ccx_id, FLAG_NAME: True}]}),
        ]

        self.assertTrue(self._check(build_progress(CCX_ID, other_ccx_id)))

    @override_settings(**ENABLED_SETTINGS)
    def test_only_exact_course_match_is_considered(self):
        """
        Partial matches returned by the API must not block issuance.
        """
        self.api_client.get.return_value = build_response(
            json_data={"results": [{"ccx_id": f"{CCX_ID}0", FLAG_NAME: False}]},
        )

        self.assertTrue(self._check(build_progress(CCX_ID)))

    @override_settings(**ENABLED_SETTINGS)
    def test_exact_match_is_used_among_multiple_results(self):
        self.api_client.get.return_value = build_response(
            json_data={
                "results": [
                    {"ccx_id": f"{CCX_ID}0", FLAG_NAME: True},
                    {"ccx_id": CCX_ID, FLAG_NAME: False},
                ]
            },
        )

        self.assertFalse(self._check(build_progress(CCX_ID)))

    @override_settings(**ENABLED_SETTINGS)
    def test_allowed_when_no_results_are_returned(self):
        self.api_client.get.return_value = build_response(json_data={"results": []})

        self.assertTrue(self._check(build_progress(CCX_ID)))

    @override_settings(**ENABLED_SETTINGS)
    def test_allowed_when_response_has_no_results_key(self):
        self.api_client.get.return_value = build_response(json_data={})

        self.assertTrue(self._check(build_progress(CCX_ID)))

    @override_settings(**ENABLED_SETTINGS)
    def test_allowed_when_flag_is_missing_from_result(self):
        self.api_client.get.return_value = build_response(json_data={"results": [{"ccx_id": CCX_ID}]})

        self.assertTrue(self._check(build_progress(CCX_ID)))

    @override_settings(**ENABLED_SETTINGS)
    def test_allowed_when_api_returns_error_status(self):
        self.api_client.get.return_value = build_response(status_code=500)

        self.assertTrue(self._check(build_progress(CCX_ID)))

    @override_settings(**ENABLED_SETTINGS)
    def test_allowed_when_api_returns_invalid_json(self):
        self.api_client.get.return_value = build_response(json_error=True)

        self.assertTrue(self._check(build_progress(CCX_ID)))

    @override_settings(**ENABLED_SETTINGS)
    def test_allowed_when_api_request_fails(self):
        self.api_client.get.side_effect = requests.ConnectionError("boom")

        self.assertTrue(self._check(build_progress(CCX_ID)))

    @override_settings(**ENABLED_SETTINGS)
    def test_request_failure_does_not_stop_remaining_checks(self):
        other_ccx_id = "ccx-v1:ORG+OTHER+RUN+ccx@2"
        self.api_client.get.side_effect = [
            requests.Timeout("timeout"),
            build_response(json_data={"results": [{"ccx_id": other_ccx_id, FLAG_NAME: False}]}),
        ]

        self.assertFalse(self._check(build_progress(CCX_ID, other_ccx_id)))
